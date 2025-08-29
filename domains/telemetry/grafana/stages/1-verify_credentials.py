import os
import sys
import json
import logging
import requests
from requests.auth import HTTPBasicAuth
import base64

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
L = logging.getLogger(__name__)

def verify_grafana_credentials():
    """
    Verify Grafana credentials by attempting to authenticate and access Grafana API.
    
    Environment variables required:
    - grafana_url: Base URL of the Grafana instance
    - grafana_api_key: API Key for authentication (OR username/password)
    - grafana_username: Username for basic auth (alternative to API key)
    - grafana_password: Password for basic auth (alternative to API key)
    - grafana_org_id: Organization ID (optional, defaults to 1)
    - grafana_api_request_timeout: Request timeout in seconds (optional, defaults to 30)
    - grafana_api_max_retries: Max retries for API requests (optional, defaults to 3)
    
    Returns:
    - True if credentials are valid and can access Grafana API
    - False otherwise
    """
    
    # Get environment variables
    grafana_url = os.environ.get('GRAFANA_URL')
    grafana_api_key = os.environ.get('GRAFANA_API_KEY')
    grafana_username = os.environ.get('GRAFANA_USERNAME')
    grafana_password = os.environ.get('GRAFANA_PASSWORD')
    grafana_org_id = int(os.environ.get('GRAFANA_ORG_ID', 1))
    grafana_api_request_timeout = int(os.environ.get('GRAFANA_API_REQUEST_TIMEOUT', 30))
    grafana_api_max_retries = int(os.environ.get('GRAFANA_API_MAX_RETRIES', 3))
    
    L.info("Retrieved environment variables")
    L.info(f"Using Grafana URL: {grafana_url}")
    L.info(f"Using organization ID: {grafana_org_id}")
    L.info(f"Request timeout: {grafana_api_request_timeout}s")
    L.info(f"Max retries: {grafana_api_max_retries}")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not grafana_url:
        missing_vars.append('GRAFANA_URL')
    
    # Check authentication method
    has_api_key = bool(grafana_api_key)
    has_basic_auth = bool(grafana_username and grafana_password)
    
    if not has_api_key and not has_basic_auth:
        missing_vars.append('GRAFANA_API_KEY or (GRAFANA_USERNAME and GRAFANA_PASSWORD)')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Determine authentication method
    if has_api_key:
        L.info("Using API key authentication")
        auth_method = "api_key"
        auth_header = f"Bearer {grafana_api_key}"
    else:
        L.info(f"Using basic authentication with username: {grafana_username}")
        auth_method = "basic"
        auth_header = None
    
    # Ensure the URL has the proper format
    if not grafana_url.startswith(('http://', 'https://')):
        L.error(f"Invalid Grafana URL format: {grafana_url}. Must start with http:// or https://")
        return False
    
    # Remove trailing slash if present
    grafana_url = grafana_url.rstrip('/')
    
    try:
        # Test Grafana API with authentication
        L.info(f"Attempting to connect to Grafana instance at: {grafana_url}")
        
        # Prepare headers
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Grafana-Org-Id': str(grafana_org_id)
        }
        
        # Add authentication
        auth = None
        if auth_method == "api_key":
            headers['Authorization'] = auth_header
        else:
            auth = HTTPBasicAuth(grafana_username, grafana_password)
        
        # Test endpoint: Get health check (lightweight call)
        test_url = f"{grafana_url}/api/health"
        
        for attempt in range(grafana_api_max_retries):
            try:
                L.info(f"Authentication attempt {attempt + 1}/{grafana_api_max_retries}")
                
                response = requests.get(
                    test_url,
                    auth=auth,
                    timeout=grafana_api_request_timeout,
                    headers=headers
                )
                
                if response.status_code == 200:
                    health_info = response.json()
                    L.info(f"Successfully connected to Grafana")
                    L.info(f"Health status: {health_info.get('database', 'Unknown')}")
                    
                    # Test authentication with user info endpoint
                    user_url = f"{grafana_url}/api/user"
                    user_response = requests.get(
                        user_url,
                        auth=auth,
                        timeout=grafana_api_request_timeout,
                        headers=headers
                    )
                    
                    if user_response.status_code == 200:
                        user_info = user_response.json()
                        L.info(f"Authenticated as user: {user_info.get('name', 'Unknown')} "
                               f"({user_info.get('email', 'Unknown')})")
                        L.info(f"User role: {user_info.get('orgRole', 'Unknown')}")
                        
                        # Test permissions by trying to get organization info
                        org_url = f"{grafana_url}/api/org"
                        org_response = requests.get(
                            org_url,
                            auth=auth,
                            timeout=grafana_api_request_timeout,
                            headers=headers
                        )
                        
                        if org_response.status_code == 200:
                            org_info = org_response.json()
                            L.info(f"Organization: {org_info.get('name', 'Unknown')} "
                                   f"(ID: {org_info.get('id', 'Unknown')})")
                            L.info("Successfully verified organization access permissions")
                            
                            # Test dashboard access
                            dashboards_url = f"{grafana_url}/api/search"
                            dashboards_response = requests.get(
                                dashboards_url,
                                auth=auth,
                                timeout=grafana_api_request_timeout,
                                headers=headers,
                                params={'limit': 1}  # Just test access, don't need all dashboards
                            )
                            
                            if dashboards_response.status_code == 200:
                                L.info("Successfully verified dashboard access permissions")
                                L.info("All credential verification tests passed")
                                return True
                            else:
                                L.error(f"Failed to access dashboards endpoint. Status: {dashboards_response.status_code}, "
                                       f"Response: {dashboards_response.text}")
                                return False
                        else:
                            L.error(f"Failed to get organization info. Status: {org_response.status_code}, "
                                   f"Response: {org_response.text}")
                            return False
                    else:
                        L.error(f"Failed to get current user info. Status: {user_response.status_code}, "
                               f"Response: {user_response.text}")
                        return False
                        
                elif response.status_code == 401:
                    L.error("Authentication failed - Invalid credentials")
                    return False
                elif response.status_code == 403:
                    L.error("Authentication failed - Access forbidden (check permissions)")
                    return False
                elif response.status_code == 404:
                    L.error("Grafana API endpoint not found - Check Grafana URL")
                    return False
                else:
                    L.warning(f"Attempt {attempt + 1} failed with status {response.status_code}: {response.text}")
                    if attempt == grafana_api_max_retries - 1:
                        L.error(f"All {grafana_api_max_retries} attempts failed")
                        return False
                    
            except requests.exceptions.Timeout:
                L.warning(f"Attempt {attempt + 1} timed out after {grafana_api_request_timeout} seconds")
                if attempt == grafana_api_max_retries - 1:
                    L.error(f"All {grafana_api_max_retries} attempts timed out")
                    return False
            except requests.exceptions.ConnectionError as e:
                L.warning(f"Attempt {attempt + 1} failed with connection error: {e}")
                if attempt == grafana_api_max_retries - 1:
                    L.error(f"All {grafana_api_max_retries} attempts failed with connection errors")
                    return False
            except requests.exceptions.RequestException as e:
                L.error(f"Request exception on attempt {attempt + 1}: {e}")
                if attempt == grafana_api_max_retries - 1:
                    return False
        
        return False
        
    except Exception as e:
        L.error(f"Unexpected exception during credential verification: {e}")
        return False

def test_grafana_api_endpoints():
    """
    Test additional Grafana API endpoints to ensure comprehensive access.
    
    Returns:
    - True if all endpoint tests pass
    - False otherwise
    """
    
    # Get environment variables
    grafana_url = os.environ.get('GRAFANA_URL').rstrip('/')
    grafana_api_key = os.environ.get('GRAFANA_API_KEY')
    grafana_username = os.environ.get('GRAFANA_USERNAME')
    grafana_password = os.environ.get('GRAFANA_PASSWORD')
    grafana_org_id = int(os.environ.get('GRAFANA_ORG_ID', 1))
    grafana_api_request_timeout = int(os.environ.get('GRAFANA_API_REQUEST_TIMEOUT', 30))
    
    # Prepare authentication
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Grafana-Org-Id': str(grafana_org_id)
    }
    
    auth = None
    if grafana_api_key:
        headers['Authorization'] = f"Bearer {grafana_api_key}"
    else:
        auth = HTTPBasicAuth(grafana_username, grafana_password)
    
    # Test endpoints that will be used by the connector
    test_endpoints = [
        {
            'name': 'Dashboards Search',
            'url': f"{grafana_url}/api/search",
            'params': {'limit': 5}
        },
        {
            'name': 'Data Sources List',
            'url': f"{grafana_url}/api/datasources",
            'params': {}
        },
        {
            'name': 'Annotations Query',
            'url': f"{grafana_url}/api/annotations",
            'params': {'limit': 1}
        },
        {
            'name': 'Folders List',
            'url': f"{grafana_url}/api/folders",
            'params': {}
        }
    ]
    
    L.info("Testing additional Grafana API endpoints...")
    
    for endpoint in test_endpoints:
        try:
            L.info(f"Testing {endpoint['name']} endpoint...")
            
            response = requests.get(
                endpoint['url'],
                auth=auth,
                timeout=grafana_api_request_timeout,
                headers=headers,
                params=endpoint.get('params', {})
            )
            
            if response.status_code == 200:
                L.info(f"✅ {endpoint['name']} endpoint test passed")
                
                # Log some basic info about the response
                try:
                    data = response.json()
                    if isinstance(data, list):
                        L.info(f"   Returned {len(data)} items")
                    elif isinstance(data, dict):
                        L.info(f"   Response keys: {list(data.keys())}")
                except:
                    L.info(f"   Response received (non-JSON)")
            else:
                L.warning(f"⚠️  {endpoint['name']} endpoint returned status {response.status_code}")
                L.warning(f"Response: {response.text}")
                
        except Exception as e:
            L.error(f"❌ {endpoint['name']} endpoint test failed: {e}")
            return False
    
    L.info("All endpoint tests completed")
    return True

def main():
    L.info("Starting Grafana credential verification")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('GRAFANA_URL'):
            os.environ['GRAFANA_URL'] = input("Enter Grafana URL (e.g., https://your-grafana.com): ")
        
        auth_method = input("Choose authentication method (1=API Key, 2=Username/Password): ")
        
        if auth_method == "1":
            if not os.environ.get('GRAFANA_API_KEY'):
                os.environ['GRAFANA_API_KEY'] = input("Enter Grafana API key: ")
        else:
            if not os.environ.get('GRAFANA_USERNAME'):
                os.environ['GRAFANA_USERNAME'] = input("Enter Grafana username: ")
            if not os.environ.get('GRAFANA_PASSWORD'):
                os.environ['GRAFANA_PASSWORD'] = input("Enter Grafana password: ")
        
        if not os.environ.get('GRAFANA_ORG_ID'):
            org_id = input("Enter organization ID (default 1): ")
            os.environ['GRAFANA_ORG_ID'] = org_id if org_id else '1'
        if not os.environ.get('GRAFANA_API_REQUEST_TIMEOUT'):
            timeout = input("Enter request timeout in seconds (default 30): ")
            os.environ['GRAFANA_API_REQUEST_TIMEOUT'] = timeout if timeout else '30'
        if not os.environ.get('GRAFANA_API_MAX_RETRIES'):
            retries = input("Enter max retries (default 3): ")
            os.environ['GRAFANA_API_MAX_RETRIES'] = retries if retries else '3'
    else:
        L.info("Using environment variables for credentials")
    
    # Basic credential verification
    L.info("\n=== Basic Credential Verification ===")
    success = verify_grafana_credentials()
    
    if not success:
        L.error("❌ Basic credential verification failed")
        return 1
    
    # Extended endpoint testing
    L.info("\n=== Extended API Endpoint Testing ===")
    endpoint_success = test_grafana_api_endpoints()
    
    if success and endpoint_success:
        L.info("✅ All Grafana credential verification tests completed successfully")
        L.info("Credentials are verified and valid")
        return 0
    elif success:
        L.warning("⚠️  Basic verification passed but some endpoint tests had issues")
        L.info("Credentials are verified and valid (with warnings)")
        return 0
    else:
        L.error("❌ Credential verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())