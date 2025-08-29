import os
import json
import logging
import sys
import requests
import base64
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sysaid_verification.log')
    ]
)
L = logging.getLogger(__name__)

def verify_sysaid_credentials():
    """
    Verify SysAid credentials by attempting to authenticate with the API.
    
    Environment variables required:
    - SYSAID_SERVER_URL: The URL of your SysAid server
    - SYSAID_ACCOUNT_ID: Your SysAid account ID
    - SYSAID_USERNAME: Your SysAid username
    - SYSAID_PASSWORD: Your SysAid password
    
    Returns:
    - True if credentials are valid and can access SysAid API
    - False otherwise
    """
    
    # Get environment variables
    server_url = os.environ.get('SYSAID_SERVER_URL')
    account_id = os.environ.get('SYSAID_ACCOUNT_ID')
    username = os.environ.get('SYSAID_USERNAME')
    password = os.environ.get('SYSAID_PASSWORD')
    
    L.info("Retrieved environment variables:")
    L.info(f"  Server URL: {server_url}")
    L.info(f"  Account ID: {account_id}")
    L.info(f"  Username: {username}")
    L.info(f"  Password: {'*' * 8 if password else None}")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not server_url:
        missing_vars.append('SYSAID_SERVER_URL')
    if not account_id:
        missing_vars.append('SYSAID_ACCOUNT_ID')
    if not username:
        missing_vars.append('SYSAID_USERNAME')
    if not password:
        missing_vars.append('SYSAID_PASSWORD')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Ensure server URL ends with a slash
    if not server_url.endswith('/'):
        server_url = server_url + '/'
    
    # SysAid API endpoints
    login_endpoint = urljoin(server_url, 'api/v1/login')
    
    # Prepare login data
    login_data = {
        'accountId': account_id,
        'userName': username,
        'password': password
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        # Attempt to authenticate with SysAid
        L.info(f"Attempting to connect to SysAid server at: {server_url}")
        
        response = requests.post(login_endpoint, json=login_data, headers=headers)
        L.debug(f"Response status code: {response.status_code}")
        
        # Check if the request was successful
        if response.status_code == 200:
            try:
                data = response.json()
                if 'sessionId' in data:
                    L.info("Authentication successful")
                    return data['sessionId']  # Return session ID for use in other functions
                else:
                    L.error("Login successful but no session ID returned")
                    return False
            except json.JSONDecodeError:
                L.error("Received successful status code but could not parse JSON response")
                L.error(f"Response content: {response.text[:500]}...")
                return False
        else:
            L.error(f"Error connecting to SysAid API. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        L.error(f"Exception occurred while connecting to SysAid: {e}")
        return False

def get_sysaid_service_requests(session_id, limit=10):
    """
    Retrieve a list of service requests (tickets) from SysAid.
    
    Args:
        session_id (str): Session ID from successful login
        limit (int): Maximum number of service requests to retrieve
        
    Returns:
        dict: JSON response containing service request information or None if failed
    """
    server_url = os.environ.get('SYSAID_SERVER_URL')
    
    # Ensure server URL ends with a slash
    if not server_url.endswith('/'):
        server_url = server_url + '/'
    
    # API endpoint to get service requests
    api_url = urljoin(server_url, f'api/v1/sr?limit={limit}')
    
    # Setup headers with session ID
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_id}'
    }
    
    try:
        L.info(f"Retrieving list of service requests (limit: {limit})...")
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                L.info(f"Successfully retrieved {len(data)} service requests")
                return data
            else:
                L.info(f"Successfully retrieved service requests")
                return data
        else:
            L.error(f"Failed to retrieve service requests. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving service requests: {e}")
        return None

def get_sysaid_assets(session_id, limit=5):
    """
    Retrieve assets from the SysAid CMDB.
    
    Args:
        session_id (str): Session ID from successful login
        limit (int): Maximum number of assets to retrieve
        
    Returns:
        dict: JSON response containing asset information or None if failed
    """
    server_url = os.environ.get('SYSAID_SERVER_URL')
    
    # Ensure server URL ends with a slash
    if not server_url.endswith('/'):
        server_url = server_url + '/'
    
    # API endpoint to get assets
    api_url = urljoin(server_url, f'api/v1/ci?limit={limit}')
    
    # Setup headers with session ID
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_id}'
    }
    
    try:
        L.info(f"Retrieving assets (limit: {limit})...")
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                L.info(f"Successfully retrieved {len(data)} assets")
                return data
            else:
                L.info(f"Successfully retrieved assets")
                return data
        else:
            L.error(f"Failed to retrieve assets. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving assets: {e}")
        return None

def get_sysaid_users(session_id, limit=5):
    """
    Retrieve users from SysAid.
    
    Args:
        session_id (str): Session ID from successful login
        limit (int): Maximum number of users to retrieve
        
    Returns:
        dict: JSON response containing user information or None if failed
    """
    server_url = os.environ.get('SYSAID_SERVER_URL')
    
    # Ensure server URL ends with a slash
    if not server_url.endswith('/'):
        server_url = server_url + '/'
    
    # API endpoint to get users
    api_url = urljoin(server_url, f'api/v1/users?limit={limit}')
    
    # Setup headers with session ID
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session_id}'
    }
    
    try:
        L.info(f"Retrieving users (limit: {limit})...")
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                L.info(f"Successfully retrieved {len(data)} users")
                return data
            else:
                L.info(f"Successfully retrieved users")
                return data
        else:
            L.error(f"Failed to retrieve users. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving users: {e}")
        return None

def test_sysaid_data_retrieval(session_id):
    """
    Test retrieving various data types from SysAid.
    
    Args:
        session_id (str): Session ID from successful login
        
    Returns:
        bool: True if tests passed, False otherwise
    """
    overall_success = True
    
    # Test retrieving service requests
    L.info("\n=== Testing Service Request Retrieval ===")
    sr_data = get_sysaid_service_requests(session_id, limit=3)
    
    if not sr_data:
        L.error("❌ Failed to retrieve service requests")
        overall_success = False
    else:
        L.info("✅ Successfully retrieved service requests")
        # Display a sample service request (truncated)
        if isinstance(sr_data, list) and len(sr_data) > 0:
            sample_sr = sr_data[0]
            # Get first few fields for sample display
            sample_fields = dict(list(sample_sr.items())[:5])
            L.info(f"Sample service request (truncated): {json.dumps(sample_fields, indent=2)}")
    
    # Test retrieving assets
    L.info("\n=== Testing Asset Retrieval ===")
    asset_data = get_sysaid_assets(session_id, limit=3)
    
    if not asset_data:
        L.error("❌ Failed to retrieve assets")
        overall_success = False
    else:
        L.info("✅ Successfully retrieved assets")
        # Display a sample asset (truncated)
        if isinstance(asset_data, list) and len(asset_data) > 0:
            sample_asset = asset_data[0]
            # Get first few fields for sample display
            sample_fields = dict(list(sample_asset.items())[:5])
            L.info(f"Sample asset (truncated): {json.dumps(sample_fields, indent=2)}")
    
    # Test retrieving users
    L.info("\n=== Testing User Retrieval ===")
    user_data = get_sysaid_users(session_id, limit=3)
    
    if not user_data:
        L.error("❌ Failed to retrieve users")
        overall_success = False
    else:
        L.info("✅ Successfully retrieved users")
        # Display a sample user (truncated)
        if isinstance(user_data, list) and len(user_data) > 0:
            sample_user = user_data[0]
            # Get first few fields for sample display
            sample_fields = dict(list(sample_user.items())[:5])
            L.info(f"Sample user (truncated): {json.dumps(sample_fields, indent=2)}")
    
    return overall_success

def main():
    L.info("Starting SysAid credential verification")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('SYSAID_SERVER_URL'):
            os.environ['SYSAID_SERVER_URL'] = input("Enter SysAid server URL: ")
        if not os.environ.get('SYSAID_ACCOUNT_ID'):
            os.environ['SYSAID_ACCOUNT_ID'] = input("Enter SysAid account ID: ")
        if not os.environ.get('SYSAID_USERNAME'):
            os.environ['SYSAID_USERNAME'] = input("Enter SysAid username: ")
        if not os.environ.get('SYSAID_PASSWORD'):
            os.environ['SYSAID_PASSWORD'] = input("Enter SysAid password: ")
    else:
        L.info("Using environment variables for credentials")
    
    # Basic credential verification
    L.info("\n=== Basic Credential Verification ===")
    session_id = verify_sysaid_credentials()
    
    if not session_id:
        L.error("Basic credential verification failed")
        return 1
    
    # Extended testing - Data retrieval
    L.info("\n=== Extended Verification: Data Retrieval ===")
    test_success = test_sysaid_data_retrieval(session_id)
    
    if test_success:
        L.info("All SysAid credential and data retrieval tests completed successfully")
        return 0
    else:
        L.warning("Basic authentication passed but some data retrieval tests failed")
        return 0  # Still return success since basic auth worked
    
if __name__ == "__main__":
    sys.exit(main())