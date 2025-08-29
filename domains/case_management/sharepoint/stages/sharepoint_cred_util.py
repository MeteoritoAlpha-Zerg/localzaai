import os
import msal
import requests
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_sharepoint_via_graph():
    """Test SharePoint connection using Microsoft Graph API"""
    
    # Get environment variables
    site_url = os.environ.get('SHAREPOINT_URL', '').rstrip('/')
    site_name = os.environ.get('SHAREPOINT_SITE_NAME', '')
    tenant_id = os.environ.get('SHAREPOINT_TENANT_ID', '')
    client_id = os.environ.get('SHAREPOINT_CLIENT_ID', '')
    client_secret = os.environ.get('SHAREPOINT_CLIENT_SECRET', '')
    
    # Prompt for any missing variables
    if not site_url:
        site_url = input("Enter your SharePoint URL (e.g., https://zergai.sharepoint.com): ").rstrip('/')
    if not site_name:
        site_name = input("Enter your SharePoint site name: ")
    if not tenant_id:
        tenant_id = input("Enter your Azure AD Tenant ID: ")
    if not client_id:
        client_id = input("Enter your Azure AD Application ID: ")
    if not client_secret:
        client_secret = input("Enter your client secret: ")
    
    # Extract the domain part of the SharePoint URL
    domain_parts = site_url.split('//')
    if len(domain_parts) > 1:
        domain = domain_parts[1]
    else:
        domain = site_url
    
    # Format the site path for Graph API
    site_path = f"{domain}:/sites/{site_name}"
    
    logger.info(f"Testing access to SharePoint site: {site_url}/sites/{site_name}")
    logger.info(f"Using Microsoft Graph API with site path: {site_path}")
    
    try:
        # Step 1: Get an access token for Microsoft Graph
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority
        )
        
        # Request token for Microsoft Graph API
        scopes = ["https://graph.microsoft.com/.default"]
        logger.info(f"Requesting access token for Microsoft Graph API")
        
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" not in result:
            logger.error(f"Failed to acquire token. Error: {result.get('error')}")
            logger.error(f"Error description: {result.get('error_description')}")
            return False
        
        logger.info("Successfully acquired access token for Microsoft Graph")
        token = result["access_token"]
        
        # Step 2: Get site information using Microsoft Graph
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_path}"
        logger.info(f"Retrieving site information from: {graph_url}")
        
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code == 200:
            site_info = response.json()
            logger.info(f"Successfully connected to SharePoint site: {site_info.get('displayName')}")
            logger.info(f"Site description: {site_info.get('description', 'N/A')}")
            logger.info(f"Web URL: {site_info.get('webUrl')}")
            
            # Step 3: List some drive items (documents)
            drive_url = f"https://graph.microsoft.com/v1.0/sites/{site_info['id']}/drives"
            logger.info(f"Retrieving document libraries from: {drive_url}")
            
            drive_response = requests.get(drive_url, headers=headers)
            
            if drive_response.status_code == 200:
                drives = drive_response.json().get('value', [])
                logger.info(f"Found {len(drives)} document libraries")
                
                if drives:
                    drive_id = drives[0]['id']
                    items_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
                    logger.info(f"Retrieving items from default document library")
                    
                    items_response = requests.get(items_url, headers=headers)
                    
                    if items_response.status_code == 200:
                        items = items_response.json().get('value', [])
                        logger.info(f"Found {len(items)} items in the document library")
                        
                        # Display first few items
                        for idx, item in enumerate(items[:5]):
                            logger.info(f"  {idx+1}. {item.get('name')} ({item.get('size', 'N/A')} bytes)")
                    else:
                        logger.warning(f"Could not retrieve items. Status: {items_response.status_code}")
                        logger.warning(f"Response: {items_response.text}")
            else:
                logger.warning(f"Could not retrieve drives. Status: {drive_response.status_code}")
                logger.warning(f"Response: {drive_response.text}")
            
            return True
            
        else:
            logger.error(f"Failed to access SharePoint site. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error during SharePoint connection test: {str(e)}")
        return False

def list_all_sharepoint_sites():
    """List all SharePoint sites the app has access to"""
    
    tenant_id = os.environ.get('SHAREPOINT_TENANT_ID', '')
    client_id = os.environ.get('SHAREPOINT_CLIENT_ID', '')
    client_secret = os.environ.get('SHAREPOINT_CLIENT_SECRET', '')
    
    # Prompt for any missing variables
    if not tenant_id:
        tenant_id = input("Enter your Azure AD Tenant ID: ")
    if not client_id:
        client_id = input("Enter your Azure AD Application ID: ")
    if not client_secret:
        client_secret = input("Enter your client secret: ")
    
    logger.info("Attempting to list all SharePoint sites accessible to the app")
    
    try:
        # Get an access token for Microsoft Graph
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority
        )
        
        # Request token for Microsoft Graph API
        scopes = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" not in result:
            logger.error(f"Failed to acquire token. Error: {result.get('error')}")
            logger.error(f"Error description: {result.get('error_description')}")
            return False
        
        logger.info("Successfully acquired access token for Microsoft Graph")
        token = result["access_token"]
        
        # List all sites in the tenant
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        # Try to get sites
        graph_url = "https://graph.microsoft.com/v1.0/sites?search=*"
        logger.info(f"Retrieving sites from: {graph_url}")
        
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code == 200:
            sites = response.json().get('value', [])
            logger.info(f"Found {len(sites)} SharePoint sites")
            
            if sites:
                logger.info("Available SharePoint sites:")
                for idx, site in enumerate(sites):
                    logger.info(f"  {idx+1}. {site.get('displayName')}")
                    logger.info(f"     URL: {site.get('webUrl')}")
                    logger.info(f"     ID: {site.get('id')}")
                    logger.info(f"     Description: {site.get('description', 'N/A')}")
                    logger.info("")
            else:
                logger.warning("No sites found. This may indicate permission issues.")
            
            return True
        else:
            logger.error(f"Failed to list sites. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error listing SharePoint sites: {str(e)}")
        return False

if __name__ == "__main__":
    print("SharePoint Access via Microsoft Graph API")
    print("========================================")
    
    # Make sure MSAL is installed
    try:
        import msal
    except ImportError:
        print("MSAL package not found. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "msal"])
        print("MSAL installed successfully.")
    
    # Ask user what they want to do
    print("\nOptions:")
    print("1. Test connection to a specific SharePoint site")
    print("2. List all SharePoint sites accessible to the app")
    
    choice = input("\nEnter your choice (1 or 2): ")
    
    if choice == "1":
        result = test_sharepoint_via_graph()
    elif choice == "2":
        result = list_all_sharepoint_sites()
    else:
        print("Invalid choice. Exiting.")
        result = False
    
    if result:
        print("\n✅ SUCCESS: Operation completed successfully!")
    else:
        print("\n❌ FAILED: Operation was not successful.")
        print("\nTroubleshooting steps:")
        print("1. Verify your Azure AD app has Microsoft Graph API permissions:")
        print("   - Sites.Read.All (for read access)")
        print("   - Sites.ReadWrite.All (for write access)")
        print("2. Ensure admin consent has been provided for the permissions")
        print("3. Check that the site URL and name are correct")
        print("4. Verify the client ID, client secret, and tenant ID are correct")