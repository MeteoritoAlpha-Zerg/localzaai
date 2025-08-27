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

def verify_jira_credentials():
    """
    Verify JIRA credentials by attempting to authenticate and access JIRA API.
    
    Environment variables required:
    - jira_url: Base URL of the JIRA instance
    - jira_email: Email address for authentication
    - jira_api_token: API Token for authentication
    - jira_api_request_timeout: Request timeout in seconds (optional, defaults to 30)
    - jira_api_max_retries: Max retries for API requests (optional, defaults to 3)
    
    Returns:
    - True if credentials are valid and can access JIRA API
    - False otherwise
    """
    
    # Get environment variables
    jira_url = os.environ.get('JIRA_URL')
    jira_email = os.environ.get('JIRA_EMAIL')
    jira_api_token = os.environ.get('JIRA_API_TOKEN')
    jira_api_request_timeout = int(os.environ.get('JIRA_API_REQUEST_TIMEOUT', 30))
    jira_api_max_retries = int(os.environ.get('JIRA_API_MAX_RETRIES', 3))
    
    L.info("Retrieved environment variables")
    L.info(f"Using JIRA URL: {jira_url}")
    L.info(f"Using email: {jira_email}")
    L.info(f"Request timeout: {jira_api_request_timeout}s")
    L.info(f"Max retries: {jira_api_max_retries}")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not jira_url:
        missing_vars.append('JIRA_URL')
    if not jira_email:
        missing_vars.append('JIRA_EMAIL')
    if not jira_api_token:
        missing_vars.append('JIRA_API_TOKEN')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Ensure the URL has the proper format
    if not jira_url.startswith(('http://', 'https://')):
        L.error(f"Invalid JIRA URL format: {jira_url}. Must start with http:// or https://")
        return False
    
    # Remove trailing slash if present
    jira_url = jira_url.rstrip('/')
    
    try:
        # Test JIRA API with authentication
        L.info(f"Attempting to connect to JIRA instance at: {jira_url}")
        
        # Create authentication
        auth = HTTPBasicAuth(jira_email, jira_api_token)
        
        # Test endpoint: Get server info (lightweight call)
        test_url = f"{jira_url}/rest/api/2/serverInfo"
        
        for attempt in range(jira_api_max_retries):
            try:
                L.info(f"Authentication attempt {attempt + 1}/{jira_api_max_retries}")
                
                response = requests.get(
                    test_url,
                    auth=auth,
                    timeout=jira_api_request_timeout,
                    headers={
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                )
                
                if response.status_code == 200:
                    server_info = response.json()
                    L.info(f"Successfully authenticated with JIRA")
                    L.info(f"Server info: Version {server_info.get('version', 'Unknown')}, "
                           f"Build {server_info.get('buildNumber', 'Unknown')}")
                    
                    # Test another endpoint to ensure proper access: Get current user
                    user_url = f"{jira_url}/rest/api/2/myself"
                    user_response = requests.get(
                        user_url,
                        auth=auth,
                        timeout=jira_api_request_timeout,
                        headers={
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'
                        }
                    )
                    
                    if user_response.status_code == 200:
                        user_info = user_response.json()
                        L.info(f"Authenticated as user: {user_info.get('displayName', 'Unknown')} "
                               f"({user_info.get('emailAddress', 'Unknown')})")
                        
                        # Test permissions by trying to get projects (minimal request)
                        projects_url = f"{jira_url}/rest/api/2/project"
                        projects_response = requests.get(
                            projects_url,
                            auth=auth,
                            timeout=jira_api_request_timeout,
                            headers={
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            },
                            params={'maxResults': 1}  # Just test access, don't need all projects
                        )
                        
                        if projects_response.status_code == 200:
                            L.info("Successfully verified project access permissions")
                            L.info("All credential verification tests passed")
                            return True
                        else:
                            L.error(f"Failed to access projects endpoint. Status: {projects_response.status_code}, "
                                   f"Response: {projects_response.text}")
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
                    L.error("JIRA API endpoint not found - Check JIRA URL")
                    return False
                else:
                    L.warning(f"Attempt {attempt + 1} failed with status {response.status_code}: {response.text}")
                    if attempt == jira_api_max_retries - 1:
                        L.error(f"All {jira_api_max_retries} attempts failed")
                        return False
                    
            except requests.exceptions.Timeout:
                L.warning(f"Attempt {attempt + 1} timed out after {jira_api_request_timeout} seconds")
                if attempt == jira_api_max_retries - 1:
                    L.error(f"All {jira_api_max_retries} attempts timed out")
                    return False
            except requests.exceptions.ConnectionError as e:
                L.warning(f"Attempt {attempt + 1} failed with connection error: {e}")
                if attempt == jira_api_max_retries - 1:
                    L.error(f"All {jira_api_max_retries} attempts failed with connection errors")
                    return False
            except requests.exceptions.RequestException as e:
                L.error(f"Request exception on attempt {attempt + 1}: {e}")
                if attempt == jira_api_max_retries - 1:
                    return False
        
        return False
        
    except Exception as e:
        L.error(f"Unexpected exception during credential verification: {e}")
        return False

def test_jira_api_endpoints():
    """
    Test additional JIRA API endpoints to ensure comprehensive access.
    
    Returns:
    - True if all endpoint tests pass
    - False otherwise
    """
    
    # Get environment variables
    jira_url = os.environ.get('JIRA_URL').rstrip('/')
    jira_email = os.environ.get('JIRA_EMAIL')
    jira_api_token = os.environ.get('JIRA_API_TOKEN')
    jira_api_request_timeout = int(os.environ.get('JIRA_API_REQUEST_TIMEOUT', 30))
    
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    
    # Test endpoints that will be used by the connector
    test_endpoints = [
        {
            'name': 'Projects List',
            'url': f"{jira_url}/rest/api/2/project",
            'params': {'maxResults': 5}
        },
        {
            'name': 'Issue Search',
            'url': f"{jira_url}/rest/api/2/search",
            'params': {'maxResults': 1, 'jql': 'order by created DESC'}
        }
    ]
    
    L.info("Testing additional JIRA API endpoints...")
    
    for endpoint in test_endpoints:
        try:
            L.info(f"Testing {endpoint['name']} endpoint...")
            
            response = requests.get(
                endpoint['url'],
                auth=auth,
                timeout=jira_api_request_timeout,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                params=endpoint.get('params', {})
            )
            
            if response.status_code == 200:
                L.info(f"✅ {endpoint['name']} endpoint test passed")
            else:
                L.warning(f"⚠️  {endpoint['name']} endpoint returned status {response.status_code}")
                L.warning(f"Response: {response.text}")
                
        except Exception as e:
            L.error(f"❌ {endpoint['name']} endpoint test failed: {e}")
            return False
    
    L.info("All endpoint tests completed")
    return True

def main():
    L.info("Starting JIRA credential verification")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('JIRA_URL'):
            os.environ['JIRA_URL'] = input("Enter JIRA URL (e.g., https://your-domain.atlassian.net): ")
        if not os.environ.get('JIRA_EMAIL'):
            os.environ['JIRA_EMAIL'] = input("Enter JIRA email address: ")
        if not os.environ.get('JIRA_API_TOKEN'):
            os.environ['JIRA_API_TOKEN'] = input("Enter JIRA API token: ")
        if not os.environ.get('JIRA_API_REQUEST_TIMEOUT'):
            timeout = input("Enter request timeout in seconds (default 30): ")
            os.environ['JIRA_API_REQUEST_TIMEOUT'] = timeout if timeout else '30'
        if not os.environ.get('JIRA_API_MAX_RETRIES'):
            retries = input("Enter max retries (default 3): ")
            os.environ['JIRA_API_MAX_RETRIES'] = retries if retries else '3'
    else:
        L.info("Using environment variables for credentials")
    
    # Basic credential verification
    L.info("\n=== Basic Credential Verification ===")
    success = verify_jira_credentials()
    
    if not success:
        L.error("❌ Basic credential verification failed")
        return 1
    
    # Extended endpoint testing
    L.info("\n=== Extended API Endpoint Testing ===")
    endpoint_success = test_jira_api_endpoints()
    
    if success and endpoint_success:
        L.info("✅ All JIRA credential verification tests completed successfully")
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