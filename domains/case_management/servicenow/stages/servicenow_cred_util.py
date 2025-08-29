import os
import json
import logging
import sys
import requests
import base64
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('servicenow_verification.log')
    ]
)
L = logging.getLogger(__name__)

def verify_servicenow_credentials():
    """
    Verify ServiceNow credentials by attempting to retrieve table information.
    
    Environment variables required:
    - SERVICENOW_INSTANCE_URL: The URL of your ServiceNow instance
    - SERVICENOW_USERNAME: Your ServiceNow username
    - SERVICENOW_PASSWORD: Your ServiceNow password
    
    Returns:
    - True if credentials are valid and can access ServiceNow API
    - False otherwise
    """
    
    # Get environment variables
    instance_url = os.environ.get('SERVICENOW_INSTANCE_URL')
    username = os.environ.get('SERVICENOW_USERNAME')
    password = os.environ.get('SERVICENOW_PASSWORD')
    
    L.info("Retrieved environment variables:")
    L.info(f"  Instance URL: {instance_url}")
    L.info(f"  Username: {username}")
    L.info(f"  Password: {password}")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not instance_url:
        missing_vars.append('SERVICENOW_INSTANCE_URL')
    if not username:
        missing_vars.append('SERVICENOW_USERNAME')
    if not password:
        missing_vars.append('SERVICENOW_PASSWORD')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Ensure instance URL ends with a slash
    if not instance_url.endswith('/'):
        instance_url = instance_url + '/'
    
    # Setup authentication
    auth = (username, password)
    
    # Setup headers
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint to test
    api_url = urljoin(instance_url, 'api/now/table/sys_db_object?sysparm_limit=1')
    
    try:
        # Attempt to connect to ServiceNow
        L.info(f"Attempting to connect to ServiceNow instance at: {instance_url}")
        
        response = requests.get(api_url, auth=auth, headers=headers)
        L.debug(f"Response status code: {response.status_code}")
        
        # Check if the request was successful
        if response.status_code == 200:
            try:
                data = response.json()
                L.info("Connection successful")
                L.debug(f"Retrieved data: {json.dumps(data, indent=2)}")
                return True
            except json.JSONDecodeError:
                L.error("Received successful status code but could not parse JSON response")
                L.error(f"Response content: {response.text[:500]}...")
                return False
        else:
            L.error(f"Error connecting to ServiceNow API. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        L.error(f"Exception occurred while connecting to ServiceNow: {e}")
        return False

def get_servicenow_tables(limit=10):
    """
    Retrieve a list of tables from ServiceNow.
    
    Args:
        limit (int): Maximum number of tables to retrieve
        
    Returns:
        dict: JSON response containing table information or None if failed
    """
    instance_url = os.environ.get('SERVICENOW_INSTANCE_URL')
    username = os.environ.get('SERVICENOW_USERNAME')
    password = os.environ.get('SERVICENOW_PASSWORD')
    
    # Ensure instance URL ends with a slash
    if not instance_url.endswith('/'):
        instance_url = instance_url + '/'
    
    # Setup authentication
    auth = (username, password)
    
    # Setup headers
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint to get table list
    api_url = urljoin(instance_url, f'api/now/table/sys_db_object?sysparm_limit={limit}')
    
    try:
        L.info(f"Retrieving list of tables (limit: {limit})...")
        response = requests.get(api_url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            L.info(f"Successfully retrieved {len(data.get('result', []))} tables")
            return data
        else:
            L.error(f"Failed to retrieve tables. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving tables: {e}")
        return None

def get_servicenow_records(table_name, limit=5):
    """
    Retrieve records from a specific table in ServiceNow.
    
    Args:
        table_name (str): Name of the table to retrieve records from
        limit (int): Maximum number of records to retrieve
        
    Returns:
        dict: JSON response containing record information or None if failed
    """
    instance_url = os.environ.get('SERVICENOW_INSTANCE_URL')
    username = os.environ.get('SERVICENOW_USERNAME')
    password = os.environ.get('SERVICENOW_PASSWORD')
    
    # Ensure instance URL ends with a slash
    if not instance_url.endswith('/'):
        instance_url = instance_url + '/'
    
    # Setup authentication
    auth = (username, password)
    
    # Setup headers
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint to get records from a table
    api_url = urljoin(instance_url, f'api/now/table/{table_name}?sysparm_limit={limit}')
    
    try:
        L.info(f"Retrieving records from table '{table_name}' (limit: {limit})...")
        response = requests.get(api_url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            L.info(f"Successfully retrieved {len(data.get('result', []))} records from '{table_name}'")
            return data
        else:
            L.error(f"Failed to retrieve records from '{table_name}'. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving records from '{table_name}': {e}")
        return None

def test_servicenow_tables_and_records():
    """
    Test retrieving tables and records from ServiceNow.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Table Retrieval ===")
    tables_data = get_servicenow_tables(limit=5)
    
    if not tables_data:
        print("❌ Failed to retrieve tables")
        return False
    
    L.info(f"✅ Successfully retrieved {len(tables_data.get('result', []))} tables")
    
    # Display table names
    table_names = [table.get('name') for table in tables_data.get('result', [])]
    L.info(f"Tables: {', '.join(table_names)}")
    
    # Test retrieving records from a common table
    L.info("\n=== Testing Record Retrieval ===")
    
    # Try common tables that most ServiceNow instances have
    common_tables = ['incident', 'sys_user', 'cmdb_ci', 'change_request']
    records_retrieved = False
    
    for table in common_tables:
        L.info(f"\nAttempting to retrieve records from '{table}' table...")
        records_data = get_servicenow_records(table, limit=3)
        
        if records_data and len(records_data.get('result', [])) > 0:
            L.info(f"✅ Successfully retrieved {len(records_data.get('result', []))} records from '{table}'")
            
            # Display a sample record (first record, first few fields)
            if len(records_data.get('result', [])) > 0:
                sample_record = records_data['result'][0]
                sample_fields = dict(list(sample_record.items())[:5])  # First 5 fields
                L.info(f"Sample record (truncated): {json.dumps(sample_fields, indent=2)}")
                
            records_retrieved = True
            break
        else:
            L.info(f"❌ Could not retrieve records from '{table}' table")
    
    if not records_retrieved:
        L.error("\n❌ Failed to retrieve records from any of the common tables")
        L.error("This might be due to permissions or the tables don't exist in your instance")
        return False
    
    return True

def main():
    L.info("Starting ServiceNow credential verification")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('SERVICENOW_INSTANCE_URL'):
            os.environ['SERVICENOW_INSTANCE_URL'] = input("Enter ServiceNow instance URL: ")
        if not os.environ.get('SERVICENOW_USERNAME'):
            os.environ['SERVICENOW_USERNAME'] = input("Enter ServiceNow username: ")
        if not os.environ.get('SERVICENOW_PASSWORD'):
            os.environ['SERVICENOW_PASSWORD'] = input("Enter ServiceNow password: ")
    else:
        L.info("Using environment variables for credentials")
    
    # Basic credential verification
    L.info("\n=== Basic Credential Verification ===")
    success = verify_servicenow_credentials()
    
    if not success:
        L.error("Basic credential verification failed")
        return 1
    
    # Extended testing - Tables and Records
    L.info("\n=== Extended Verification: Tables and Records ===")
    test_success = test_servicenow_tables_and_records()
    
    if success and test_success:
        L.info("All credential verification tests completed successfully")
        return 0
    elif success:
        L.warning("Basic verification passed but table/record tests failed")
        return 0  # Still return success since basic auth worked
    else:
        L.error("Credential verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())