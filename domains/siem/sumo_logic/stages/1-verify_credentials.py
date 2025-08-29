import os
import sys
import json
import logging
import requests
import base64
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sumologic_verification.log')
    ]
)
L = logging.getLogger(__name__)

class SumoLogicAPI:
    """
    Simple Sumo Logic API client for credential verification and basic operations.
    """
    
    def __init__(self, url, access_id, access_key, verify_ssl=True, timeout=30):
        """
        Initialize Sumo Logic API client.
        
        Args:
            url (str): Sumo Logic API base URL
            access_id (str): Access ID for authentication
            access_key (str): Access key for authentication
            verify_ssl (bool): Whether to verify SSL certificates
            timeout (int): Request timeout in seconds
        """
        self.base_url = url.rstrip('/')
        if not self.base_url.endswith('/api'):
            self.base_url += '/api'
            
        self.access_id = access_id
        self.access_key = access_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        # Setup authentication
        self.auth = HTTPBasicAuth(access_id, access_key)
        
        # Setup session with common headers
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.session.auth = self.auth
        self.session.verify = verify_ssl

    def _make_request(self, method, endpoint, **kwargs):
        """
        Make an authenticated request to the Sumo Logic API.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response: Response object
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        L.debug(f"Making {method} request to: {url}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            L.debug(f"Response status: {response.status_code}")
            L.debug(f"Response headers: {dict(response.headers)}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            L.error(f"Request failed: {e}")
            raise

    def test_connection(self):
        """
        Test the connection by getting collectors information (since /v1/account doesn't exist).
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            L.info("Testing Sumo Logic API connection...")
            
            # Use collectors endpoint instead of account endpoint (which doesn't exist)
            response = self._make_request('GET', '/v1/collectors', params={'limit': 1})
            
            if response.status_code == 200:
                collectors_info = response.json()
                collectors = collectors_info.get('collectors', [])
                L.info("✅ Connection test successful")
                L.info(f"Found {len(collectors)} collectors (showing first 1 for test)")
                
                # Also test getting personal folder to verify permissions
                try:
                    folder_response = self._make_request('GET', '/v2/content/folders/personal')
                    if folder_response.status_code == 200:
                        folder_info = folder_response.json()
                        L.info(f"✅ Content API access verified - Personal folder: {folder_info.get('name', 'Unknown')}")
                except Exception as e:
                    L.warning(f"⚠️  Content API test failed (may be limited permissions): {e}")
                
                return True
            else:
                L.error(f"❌ Connection test failed with status {response.status_code}")
                L.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            L.error(f"❌ Connection test failed with exception: {e}")
            return False

    def get_collectors(self, limit=10):
        """
        Get list of collectors.
        
        Args:
            limit (int): Maximum number of collectors to return
            
        Returns:
            list: List of collector information or None if failed
        """
        try:
            L.info(f"Retrieving collectors (limit: {limit})...")
            response = self._make_request('GET', '/v1/collectors', params={'limit': limit})
            
            if response.status_code == 200:
                data = response.json()
                collectors = data.get('collectors', [])
                L.info(f"✅ Successfully retrieved {len(collectors)} collectors")
                return collectors
            else:
                L.error(f"❌ Failed to retrieve collectors: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception retrieving collectors: {e}")
            return None

    def get_sources(self, collector_id, limit=10):
        """
        Get sources for a specific collector.
        
        Args:
            collector_id (int): Collector ID
            limit (int): Maximum number of sources to return
            
        Returns:
            list: List of source information or None if failed
        """
        try:
            L.info(f"Retrieving sources for collector {collector_id} (limit: {limit})...")
            response = self._make_request('GET', f'/v1/collectors/{collector_id}/sources', params={'limit': limit})
            
            if response.status_code == 200:
                data = response.json()
                sources = data.get('sources', [])
                L.info(f"✅ Successfully retrieved {len(sources)} sources for collector {collector_id}")
                return sources
            else:
                L.error(f"❌ Failed to retrieve sources: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception retrieving sources: {e}")
            return None

    def search_logs(self, query, from_time, to_time, time_zone="UTC", by_receipt_time=False):
        """
        Execute a search query using the Search Job API.
        Note: Search Job API requires cookies to be maintained across requests.
        
        Args:
            query (str): Search query
            from_time (str): Start time (ISO format)
            to_time (str): End time (ISO format)
            time_zone (str): Time zone
            by_receipt_time (bool): Whether to search by receipt time
            
        Returns:
            dict: Search job information or None if failed
        """
        try:
            L.info(f"Starting search query: {query}")
            
            search_payload = {
                "query": query,
                "from": from_time,
                "to": to_time,
                "timeZone": time_zone,
                "byReceiptTime": by_receipt_time
            }
            
            # Use session to maintain cookies (required by Search Job API)
            response = self._make_request('POST', '/v1/search/jobs', json=search_payload)
            
            if response.status_code == 202:  # Accepted
                # Extract job ID from Location header or response body
                job_id = None
                if 'Location' in response.headers:
                    location = response.headers['Location']
                    job_id = location.split('/')[-1]
                else:
                    # Try to get from response body
                    try:
                        job_data = response.json()
                        job_id = job_data.get('id')
                    except:
                        pass
                
                if job_id:
                    L.info(f"✅ Search job created with ID: {job_id}")
                    return {'id': job_id}
                else:
                    L.error("❌ Could not extract job ID from response")
                    return None
            else:
                L.error(f"❌ Failed to create search job: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception creating search job: {e}")
            return None

    def get_search_job_status(self, job_id):
        """
        Get the status of a search job.
        
        Args:
            job_id (str): Search job ID
            
        Returns:
            dict: Job status information or None if failed
        """
        try:
            response = self._make_request('GET', f'/v1/search/jobs/{job_id}')
            
            if response.status_code == 200:
                return response.json()
            else:
                L.error(f"❌ Failed to get job status: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception getting job status: {e}")
            return None

    def get_search_results(self, job_id, offset=0, limit=100):
        """
        Get results from a completed search job.
        
        Args:
            job_id (str): Search job ID
            offset (int): Result offset
            limit (int): Maximum results to return
            
        Returns:
            dict: Search results or None if failed
        """
        try:
            response = self._make_request('GET', f'/v1/search/jobs/{job_id}/messages', 
                                        params={'offset': offset, 'limit': limit})
            
            if response.status_code == 200:
                return response.json()
            else:
                L.error(f"❌ Failed to get search results: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception getting search results: {e}")
            return None

    def get_content_folders(self, limit=10):
        """
        Get content folders to test Content Management API access.
        
        Args:
            limit (int): Maximum number of folders to return
            
        Returns:
            list: List of folder information or None if failed
        """
        try:
            L.info(f"Retrieving content folders (limit: {limit})...")
            
            # Get personal folder first
            response = self._make_request('GET', '/v2/content/folders/personal')
            
            if response.status_code == 200:
                personal_folder = response.json()
                L.info(f"✅ Personal folder access confirmed: {personal_folder.get('name', 'Personal')}")
                
                # Try to get child folders
                try:
                    children_response = self._make_request('GET', f"/v2/content/{personal_folder['id']}/children", 
                                                         params={'limit': limit})
                    if children_response.status_code == 200:
                        children_data = children_response.json()
                        children = children_data.get('children', [])
                        L.info(f"✅ Found {len(children)} items in personal folder")
                        return [personal_folder] + children
                    else:
                        return [personal_folder]
                except Exception as e:
                    L.warning(f"Could not retrieve folder children: {e}")
                    return [personal_folder]
            else:
                L.error(f"❌ Failed to retrieve content folders: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            L.error(f"❌ Exception retrieving content folders: {e}")
            return None

def verify_sumologic_credentials():
    """
    Verify Sumo Logic credentials by attempting to authenticate and access basic resources.
    
    Environment variables required:
    - SUMOLOGIC_URL: Sumo Logic API base URL
    - SUMOLOGIC_ACCESS_ID: Access ID for authentication
    - SUMOLOGIC_ACCESS_KEY: Access key for authentication
    
    Returns:
        bool: True if credentials are valid, False otherwise
    """
    
    # Get environment variables
    url = os.environ.get('SUMOLOGIC_URL')
    access_id = os.environ.get('SUMOLOGIC_ACCESS_ID')
    access_key = os.environ.get('SUMOLOGIC_ACCESS_KEY')
    verify_ssl = os.environ.get('SUMOLOGIC_VERIFY_SSL', 'true').lower() == 'true'
    timeout = int(os.environ.get('SUMOLOGIC_API_REQUEST_TIMEOUT', '30'))
    
    L.info("Retrieved environment variables")
    L.info(f"Using URL: {url}")
    L.info(f"Using Access ID: {access_id[:8]}..." if access_id else "No Access ID")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not url:
        missing_vars.append('SUMOLOGIC_URL')
    if not access_id:
        missing_vars.append('SUMOLOGIC_ACCESS_ID')
    if not access_key:
        missing_vars.append('SUMOLOGIC_ACCESS_KEY')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    try:
        # Create Sumo Logic API client
        sumo = SumoLogicAPI(url, access_id, access_key, verify_ssl, timeout)
        
        # Test basic connection
        if not sumo.test_connection():
            return False
        
        # Test getting collectors
        L.info("\n=== Testing Collector Management API ===")
        collectors = sumo.get_collectors(limit=5)
        
        if collectors is not None:
            L.info(f"✅ Successfully retrieved {len(collectors)} collectors")
            
            # Display collector information
            for collector in collectors[:3]:  # Show first 3
                L.info(f"Collector: {collector.get('name')} (ID: {collector.get('id')}, Type: {collector.get('collectorType')})")
        else:
            L.warning("❌ Failed to retrieve collectors or no collectors found")
        
        # Test getting sources if we have collectors
        if collectors and len(collectors) > 0:
            L.info("\n=== Testing Source Management API ===")
            test_collector_id = collectors[0]['id']
            sources = sumo.get_sources(test_collector_id, limit=5)
            
            if sources is not None:
                L.info(f"✅ Successfully retrieved {len(sources)} sources from collector {test_collector_id}")
                
                # Display source information
                for source in sources[:3]:  # Show first 3
                    L.info(f"Source: {source.get('name')} (ID: {source.get('id')}, Type: {source.get('sourceType')})")
            else:
                L.warning(f"❌ Failed to retrieve sources from collector {test_collector_id}")
        
        # Test Content Management API
        L.info("\n=== Testing Content Management API ===")
        folders = sumo.get_content_folders(limit=5)
        
        if folders is not None:
            L.info(f"✅ Successfully accessed content management - found {len(folders)} items")
        else:
            L.warning("❌ Failed to access content management API")
        
        # Test a simple search query (Note: this may fail on trial accounts or if no data exists)
        L.info("\n=== Testing Search Job API ===")
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        search_job = sumo.search_logs(
            query="*",
            from_time=start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            to_time=end_time.strftime('%Y-%m-%dT%H:%M:%S')
        )
        
        if search_job:
            job_id = search_job.get('id')
            L.info(f"✅ Search job created successfully with ID: {job_id}")
            
            # Check job status
            import time
            max_wait = 30  # seconds
            wait_time = 0
            
            while wait_time < max_wait:
                status = sumo.get_search_job_status(job_id)
                if status:
                    state = status.get('state')
                    L.info(f"Job status: {state}")
                    
                    if state == 'DONE GATHERING RESULTS':
                        L.info("✅ Search completed successfully")
                        
                        # Try to get some results
                        results = sumo.get_search_results(job_id, limit=5)
                        if results:
                            messages = results.get('messages', [])
                            L.info(f"✅ Retrieved {len(messages)} sample results")
                        break
                    elif state in ['CANCELLED', 'FORCE PAUSED']:
                        L.warning(f"⚠️ Search job was {state}")
                        break
                
                time.sleep(2)
                wait_time += 2
            
            if wait_time >= max_wait:
                L.warning("⚠️ Search job did not complete within timeout")
        else:
            L.warning("❌ Failed to create search job (may be due to trial account limitations or no data)")
        
        L.info("\n✅ All credential verification tests completed successfully!")
        return True
        
    except Exception as e:
        L.error(f"❌ Exception during verification: {e}")
        return False

def main():
    print("Starting Sumo Logic credential verification")
    L.info("Starting Sumo Logic credential verification")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('SUMOLOGIC_URL'):
            print("\nCommon Sumo Logic API endpoints:")
            print("- US1: https://api.sumologic.com/api")
            print("- US2: https://api.us2.sumologic.com/api")
            print("- EU: https://api.eu.sumologic.com/api")
            print("- AU: https://api.au.sumologic.com/api")
            print("- CA: https://api.ca.sumologic.com/api")
            print("- DE: https://api.de.sumologic.com/api")
            print("- JP: https://api.jp.sumologic.com/api")
            os.environ['SUMOLOGIC_URL'] = input("\nEnter Sumo Logic API URL: ")
            
        if not os.environ.get('SUMOLOGIC_ACCESS_ID'):
            os.environ['SUMOLOGIC_ACCESS_ID'] = input("Enter Access ID: ")
            
        if not os.environ.get('SUMOLOGIC_ACCESS_KEY'):
            os.environ['SUMOLOGIC_ACCESS_KEY'] = input("Enter Access Key: ")
            
        # Set optional environment variables with defaults
        os.environ.setdefault('SUMOLOGIC_VERIFY_SSL', 'true')
        os.environ.setdefault('SUMOLOGIC_API_REQUEST_TIMEOUT', '30')
    else:
        L.info("Using environment variables for credentials")
    
    # Verify credentials
    success = verify_sumologic_credentials()
    
    if success:
        L.info("Sumo Logic credential verification completed successfully!")
        return 0
    else:
        L.error("Sumo Logic credential verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())