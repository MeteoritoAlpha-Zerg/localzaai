import os
import requests
import json
import logging
from urllib.parse import urljoin
import sys
import base64
from simple_salesforce import Salesforce
from requests.exceptions import ConnectionError, Timeout

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('salesforce_verification.log')
    ]
)
L = logging.getLogger(__name__)

def verify_salesforce_credentials():
    """
    Verify Salesforce credentials by attempting to authenticate and get instance information.
    
    Environment variables required:
    - SALESFORCE_USERNAME: Your Salesforce username (email)
    - SALESFORCE_PASSWORD: Your Salesforce password
    - SALESFORCE_SECURITY_TOKEN: Your Salesforce security token
    - SALESFORCE_DOMAIN: Optional domain (e.g., 'test' for test.salesforce.com)
    
    Returns:
    - True if credentials are valid and can access Salesforce API
    - False otherwise
    """
    
    # Get environment variables
    username = os.environ.get('SALESFORCE_USERNAME')
    password = os.environ.get('SALESFORCE_PASSWORD')
    security_token = os.environ.get('SALESFORCE_SECURITY_TOKEN')
    domain = os.environ.get('SALESFORCE_DOMAIN', 'login')  
    
    # FIX: Strip .salesforce.com if present in the domain
    if domain.endswith('.salesforce.com'):
        domain = domain.replace('.salesforce.com', '')
    
    L.info("Retrieved environment variables")
    L.info(f"Using domain: {domain}")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not username:
        missing_vars.append('SALESFORCE_USERNAME')
    if not password:
        missing_vars.append('SALESFORCE_PASSWORD')
    if not security_token:
        missing_vars.append('SALESFORCE_SECURITY_TOKEN')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    try:
        # Attempt to connect to Salesforce
        L.info(f"Attempting to connect to Salesforce with username: {username}")
        
        # Initialize Salesforce connection
        # FIX: Don't provide domain parameter directly - simple_salesforce adds .salesforce.com automatically
        if domain == 'login':
            # For production environment
            sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token
            )
        else:
            # For sandbox or other environments
            sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
        
        # If we get here, authentication was successful
        L.info("Authentication successful")
        L.info(f"Connected to Salesforce instance: {sf.sf_instance}")
        
        # Get basic instance info
        user_info = sf.query("SELECT Id, Name, Username FROM User WHERE Username = '{}'".format(username))
        if user_info['totalSize'] > 0:
            L.info(f"Logged in as: {user_info['records'][0]['Name']} ({user_info['records'][0]['Id']})")
        
        return True
        
    except ConnectionError as e:
        L.error(f"Connection error: {e}")
        return False
    except Timeout as e:
        L.error(f"Connection timeout: {e}")
        return False
    except Exception as e:
        error_msg = f"Exception occurred while connecting to Salesforce: {e}"
        L.error(error_msg)
        return False

def get_salesforce_objects(limit=10):
    """
    Retrieve a list of available objects from Salesforce.
    
    Args:
        limit (int): Maximum number of objects to retrieve
        
    Returns:
        list: List of object information or None if failed
    """
    try:
        username = os.environ.get('SALESFORCE_USERNAME')
        password = os.environ.get('SALESFORCE_PASSWORD')
        security_token = os.environ.get('SALESFORCE_SECURITY_TOKEN')
        domain = os.environ.get('SALESFORCE_DOMAIN', 'login')
        
        # FIX: Strip .salesforce.com if present in the domain
        if domain.endswith('.salesforce.com'):
            domain = domain.replace('.salesforce.com', '')
        
        # Apply the same fix for the domain handling
        if domain == 'login':
            # For production environment
            sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token
            )
        else:
            # For sandbox or other environments
            sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
        
        L.info(f"Retrieving list of objects...")
        
        # Get object descriptions for standard and custom objects
        standard_objects = ['Account', 'Contact', 'Lead', 'Opportunity', 'Case', 
                          'User', 'Campaign', 'Contract', 'Product2']
        
        # Only take up to the limit
        selected_objects = standard_objects[:min(limit, len(standard_objects))]
        
        object_info = []
        for obj_name in selected_objects:
            try:
                # Get object metadata
                metadata = getattr(sf, obj_name).describe()
                
                # Extract useful info
                obj_info = {
                    'name': metadata['name'],
                    'label': metadata['label'],
                    'keyPrefix': metadata.get('keyPrefix'),
                    'custom': metadata['custom'],
                    'fields': len(metadata['fields'])
                }
                
                object_info.append(obj_info)
                L.info(f"Retrieved information for {obj_name}")
                
            except Exception as e:
                L.warning(f"Could not retrieve metadata for {obj_name}: {e}")
        
        L.info(f"Successfully retrieved information for {len(object_info)} objects")
        return object_info
        
    except Exception as e:
        L.error(f"Exception while retrieving objects: {e}")
        return None

def get_salesforce_records(object_name, limit=5):
    """
    Retrieve records from a specific object in Salesforce.
    
    Args:
        object_name (str): Name of the object to retrieve records from
        limit (int): Maximum number of records to retrieve
        
    Returns:
        list: List of records or None if failed
    """
    try:
        username = os.environ.get('SALESFORCE_USERNAME')
        password = os.environ.get('SALESFORCE_PASSWORD')
        security_token = os.environ.get('SALESFORCE_SECURITY_TOKEN')
        domain = os.environ.get('SALESFORCE_DOMAIN', 'login')
        
        # FIX: Strip .salesforce.com if present in the domain
        if domain.endswith('.salesforce.com'):
            domain = domain.replace('.salesforce.com', '')
        
        # Apply the same fix for the domain handling
        if domain == 'login':
            # For production environment
            sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token
            )
        else:
            # For sandbox or other environments
            sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
        
        L.info(f"Retrieving records from object '{object_name}' (limit: {limit})...")
        
        # Describe the object to get fields
        object_desc = getattr(sf, object_name).describe()
        fields = [field['name'] for field in object_desc['fields'][:10]]  # Get first 10 fields
        
        # Construct query
        query = f"SELECT {', '.join(fields)} FROM {object_name} LIMIT {limit}"
        L.debug(f"Executing query: {query}")
        
        # Execute query
        result = sf.query(query)
        
        if result['totalSize'] > 0:
            L.info(f"Successfully retrieved {result['totalSize']} records from '{object_name}'")
            return result['records']
        else:
            L.warning(f"No records found in '{object_name}'")
            return []
            
    except Exception as e:
        L.error(f"Exception while retrieving records from '{object_name}': {e}")
        return None

def test_salesforce_objects_and_records():
    """
    Test retrieving objects and records from Salesforce.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Object Retrieval ===")
    objects_data = get_salesforce_objects(limit=5)
    
    if not objects_data:
        print("❌ Failed to retrieve objects")
        return False
    
    L.info(f"✅ Successfully retrieved {len(objects_data)} objects")
    
    # Display object names
    object_names = [obj.get('name') for obj in objects_data]
    L.info(f"Objects: {', '.join(object_names)}")
    
    # Test retrieving records from common objects
    L.info("\n=== Testing Record Retrieval ===")
    
    # Try common objects that most Salesforce instances have
    common_objects = ['Account', 'Contact', 'Lead', 'Opportunity']
    records_retrieved = False
    
    for obj in common_objects:
        L.info(f"\nAttempting to retrieve records from '{obj}' object...")
        records_data = get_salesforce_records(obj, limit=3)
        
        if records_data and len(records_data) > 0:
            L.info(f"✅ Successfully retrieved {len(records_data)} records from '{obj}'")
            
            # Display a sample record (first record, simplified)
            if len(records_data) > 0:
                sample_record = records_data[0]
                # Remove attributes and keep only first few fields
                if 'attributes' in sample_record:
                    del sample_record['attributes']
                sample_fields = dict(list(sample_record.items())[:5])  # First 5 fields
                L.info(f"Sample record (truncated): {json.dumps(sample_fields, indent=2)}")
                
            records_retrieved = True
            break
        else:
            L.info(f"❌ Could not retrieve records from '{obj}' object or object is empty")
    
    if not records_retrieved:
        L.error("\n❌ Failed to retrieve records from any of the common objects")
        L.error("This might be due to permissions or the objects don't have data in your instance")
        return False
    
    return True

def main():
    L.info("Starting Salesforce credential verification")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('SALESFORCE_USERNAME'):
            os.environ['SALESFORCE_USERNAME'] = input("Enter Salesforce username: ")
        if not os.environ.get('SALESFORCE_PASSWORD'):
            os.environ['SALESFORCE_PASSWORD'] = input("Enter Salesforce password: ")
        if not os.environ.get('SALESFORCE_SECURITY_TOKEN'):
            os.environ['SALESFORCE_SECURITY_TOKEN'] = input("Enter Salesforce security token: ")
        if not os.environ.get('SALESFORCE_DOMAIN'):
            domain = input("Enter Salesforce domain (default 'login' for production, 'test' for sandbox): ")
            if domain:
                # Strip .salesforce.com if the user entered it
                if domain.endswith('.salesforce.com'):
                    domain = domain.replace('.salesforce.com', '')
                os.environ['SALESFORCE_DOMAIN'] = domain
    else:
        L.info("Using environment variables for credentials")
        
        # Strip .salesforce.com from the domain if present in environment variable
        if os.environ.get('SALESFORCE_DOMAIN', '').endswith('.salesforce.com'):
            os.environ['SALESFORCE_DOMAIN'] = os.environ['SALESFORCE_DOMAIN'].replace('.salesforce.com', '')
            L.info(f"Adjusted SALESFORCE_DOMAIN to: {os.environ['SALESFORCE_DOMAIN']}")
    
    # Basic credential verification
    L.info("\n=== Basic Credential Verification ===")
    success = verify_salesforce_credentials()
    
    if not success:
        L.error("Basic credential verification failed")
        return 1
    
    # Extended testing - Objects and Records
    L.info("\n=== Extended Verification: Objects and Records ===")
    test_success = test_salesforce_objects_and_records()
    
    if success and test_success:
        L.info("All credential verification tests completed successfully")
        return 0
    elif success:
        L.warning("Basic verification passed but object/record tests failed")
        return 0  # Still return success since basic auth worked
    else:
        L.error("Credential verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())