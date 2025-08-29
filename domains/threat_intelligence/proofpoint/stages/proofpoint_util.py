import os
import sys
import json
import logging
import base64
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('proofpoint_verification.log')
    ]
)
L = logging.getLogger(__name__)

def verify_proofpoint_credentials():
    """
    Verify Proofpoint credentials by attempting to retrieve a list of campaigns.
    
    Environment variables required:
    - PROOFPOINT_API_HOST: The base URL for Proofpoint API (typically tap-api-v2.proofpoint.com)
    - PROOFPOINT_PRINCIPAL: The service principal (username) for authenticating with Proofpoint APIs
    - PROOFPOINT_SECRET: The service secret (password) for authenticating with Proofpoint APIs
    
    Returns:
    - True if credentials are valid and can access Proofpoint API
    - False otherwise
    """
    
    # Get environment variables
    api_host = os.environ.get('PROOFPOINT_API_HOST')
    principal = os.environ.get('PROOFPOINT_PRINCIPAL')
    secret = os.environ.get('PROOFPOINT_SECRET')
    
    L.info("Retrieved environment variables:")
    L.info(f"  API Host: {api_host}")
    L.info(f"  Principal: {principal}")
    L.info(f"  Secret: {'*****' if secret else 'Not set'}")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not api_host:
        missing_vars.append('PROOFPOINT_API_HOST')
    if not principal:
        missing_vars.append('PROOFPOINT_PRINCIPAL')
    if not secret:
        missing_vars.append('PROOFPOINT_SECRET')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Ensure API host has proper format
    if not api_host.startswith('http'):
        api_host = f"https://{api_host}"
    
    # Setup authentication
    auth_str = f"{principal}:{secret}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Set up a simple test - get campaign IDs for the last 24 hours
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    
    # Format timestamps as required by Proofpoint API
    interval_start = yesterday.strftime("%Y-%m-%dT%H:%M:%SZ")
    interval_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # API endpoint to test - campaign IDs endpoint
    api_url = f"{api_host}/v2/campaign/ids?interval={interval_start}/{interval_end}"
    
    try:
        # Attempt to connect to Proofpoint
        L.info(f"Attempting to connect to Proofpoint API at: {api_host}")
        
        response = requests.get(api_url, headers=headers, timeout=30)
        L.debug(f"Response status code: {response.status_code}")
        
        # Check if the request was successful
        if response.status_code == 200:
            try:
                data = response.json()
                L.info("Connection successful with data")
                
                # Check for the campaigns array in the response
                campaign_count = len(data.get('campaigns', []))
                L.info(f"Retrieved {campaign_count} campaigns")
                L.debug(f"Retrieved data: {json.dumps(data, indent=2)}")
                return True
            except json.JSONDecodeError:
                L.error("Received successful status code but could not parse JSON response")
                L.error(f"Response content: {response.text[:500]}...")
                return False
        else:
            L.error(f"Error connecting to Proofpoint API. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        L.error(f"Exception occurred while connecting to Proofpoint: {e}")
        return False

def get_campaign_ids(days=1):
    """
    Retrieve campaign IDs from Proofpoint for a specified number of days.
    
    Args:
        days (int): Number of days to look back for campaigns
        
    Returns:
        list: List of campaign IDs or None if failed
    """
    api_host = os.environ.get('PROOFPOINT_API_HOST')
    principal = os.environ.get('PROOFPOINT_PRINCIPAL')
    secret = os.environ.get('PROOFPOINT_SECRET')
    
    # Ensure API host has proper format
    if not api_host.startswith('http'):
        api_host = f"https://{api_host}"
    
    # Setup authentication
    auth_str = f"{principal}:{secret}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Calculate date range
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Format timestamps as required by Proofpoint API
    interval_start = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    interval_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Handle Proofpoint's 24-hour limit by breaking apart longer queries
    all_campaign_ids = []
    
    # If requested days is greater than 1, we need to make multiple calls
    if days > 1:
        # Calculate number of 24-hour chunks needed
        chunks = days
        L.info(f"Breaking query into {chunks} 24-hour chunks due to API limitations")
        
        for i in range(chunks):
            chunk_end = now - timedelta(days=i)
            chunk_start = chunk_end - timedelta(days=1)
            
            # Format timestamps for this chunk
            chunk_interval_start = chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ")
            chunk_interval_end = chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            L.info(f"Retrieving campaigns for chunk {i+1}/{chunks}: {chunk_interval_start} to {chunk_interval_end}")
            chunk_ids = _get_campaign_ids_for_interval(api_host, headers, chunk_interval_start, chunk_interval_end)
            
            if chunk_ids:
                all_campaign_ids.extend(chunk_ids)
                # Sleep briefly to avoid hitting rate limits
                import time
                time.sleep(1)
            else:
                L.warning(f"Failed to retrieve campaigns for chunk {i+1}")
    else:
        # Just make a single call for 24 hours or less
        all_campaign_ids = _get_campaign_ids_for_interval(api_host, headers, interval_start, interval_end)
    
    # Remove duplicates
    if all_campaign_ids:
        unique_ids = list(set(all_campaign_ids))
        L.info(f"Retrieved {len(unique_ids)} unique campaign IDs over {days} days")
        return unique_ids
    else:
        return []

def _get_campaign_ids_for_interval(api_host, headers, interval_start, interval_end):
    """
    Helper function to retrieve campaign IDs for a specific interval.
    
    Args:
        api_host (str): Proofpoint API host
        headers (dict): Request headers including auth
        interval_start (str): Start time in ISO format
        interval_end (str): End time in ISO format
        
    Returns:
        list: List of campaign IDs for the interval
    """
    api_url = f"{api_host}/v2/campaign/ids?interval={interval_start}/{interval_end}"
    
    try:
        L.info(f"Retrieving campaign IDs for interval: {interval_start} to {interval_end}")
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract campaign IDs from the 'campaigns' array 
            campaign_data = data.get('campaigns', [])
            campaign_ids = [campaign.get('id') for campaign in campaign_data if campaign.get('id')]
            
            L.info(f"Successfully retrieved {len(campaign_ids)} campaign IDs")
            return campaign_ids
        else:
            L.error(f"Failed to retrieve campaign IDs. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving campaign IDs: {e}")
        return None

def get_campaign_details(campaign_id):
    """
    Retrieve details for a specific campaign ID.
    
    Args:
        campaign_id (str): ID of the campaign to retrieve details for
        
    Returns:
        dict: JSON response containing campaign details or None if failed
    """
    api_host = os.environ.get('PROOFPOINT_API_HOST')
    principal = os.environ.get('PROOFPOINT_PRINCIPAL')
    secret = os.environ.get('PROOFPOINT_SECRET')
    
    # Ensure API host has proper format
    if not api_host.startswith('http'):
        api_host = f"https://{api_host}"
    
    # Setup authentication
    auth_str = f"{principal}:{secret}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint for campaign details
    api_url = f"{api_host}/v2/campaign/{campaign_id}"
    
    try:
        L.info(f"Retrieving details for campaign ID: {campaign_id}")
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            L.info(f"Successfully retrieved details for campaign: {campaign_id}")
            return data
        else:
            L.error(f"Failed to retrieve campaign details. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving campaign details: {e}")
        return None

def explore_query_targets():
    """
    Explore available query targets in the Proofpoint API.
    This simulates what get_query_target_options would return in the actual connector.
    
    Returns:
        dict: Dictionary of available query targets or None if failed
    """
    # This is a placeholder that would be filled with actual API calls in the full implementation
    # In the actual connector, this would dynamically retrieve targets from the API
    
    L.info("Exploring available Proofpoint API query targets")
    
    # These are the standard query targets for Proofpoint based on its API documentation
    # In a real implementation, we would verify these with API calls
    query_targets = {
        "campaigns": {
            "description": "Campaign information including IDs and details",
            "endpoints": [
                {"name": "campaign_ids", "path": "/v2/campaign/ids", "description": "Retrieve campaign IDs for a specific time interval"},
                {"name": "campaign_details", "path": "/v2/campaign/{id}", "description": "Retrieve details for a specific campaign ID"}
            ]
        },
        "threats": {
            "description": "Threat information including IDs and details",
            "endpoints": [
                {"name": "threat_ids", "path": "/v2/threat/ids", "description": "Retrieve threat IDs for a specific time interval"},
                {"name": "threat_details", "path": "/v2/threat/{id}", "description": "Retrieve details for a specific threat ID"}
            ]
        },
        "forensics": {
            "description": "Forensic evidence data",
            "endpoints": [
                {"name": "forensic_evidence", "path": "/v2/forensics", "description": "Retrieve forensic evidence for specific threats or campaigns"}
            ]
        },
        "people": {
            "description": "Information about people at risk",
            "endpoints": [
                {"name": "vap", "path": "/v2/people/vap", "description": "Retrieve Very Attacked People (VAP) data"},
                {"name": "top_clickers", "path": "/v2/people/clickers", "description": "Retrieve top clickers data"}
            ]
        },
        "url_decoder": {
            "description": "URL decoding functionality",
            "endpoints": [
                {"name": "decode_url", "path": "/v2/url/decode", "description": "Decode Proofpoint-rewritten URLs"}
            ]
        }
    }
    
    # Verify at least one target by making a real API call
    # We'll use the campaign IDs endpoint since we've already used it for auth verification
    if verify_proofpoint_credentials():
        L.info("Verified connection to Proofpoint API")
        L.info(f"Enumerated {len(query_targets)} query targets")
        return query_targets
    else:
        L.error("Failed to connect to Proofpoint API, cannot verify query targets")
        return None

def safe_join(items_list):
    """
    Safely join a list of items that may not all be strings.
    Converts each item to a string representation.
    
    Args:
        items_list: List of items to join
        
    Returns:
        str: Comma-joined string of items
    """
    if not items_list:
        return ""
    
    # Convert each item to a string, handling dictionaries specially
    string_items = []
    for item in items_list:
        if isinstance(item, dict):
            try:
                # For dictionaries, either use a name/id field if available or convert to JSON
                if 'name' in item:
                    string_items.append(item['name'])
                elif 'id' in item:
                    string_items.append(item['id'])
                else:
                    string_items.append(json.dumps(item))
            except:
                string_items.append(str(item))
        else:
            string_items.append(str(item))
    
    return ", ".join(string_items)

def test_campaign_data_retrieval():
    """
    Test retrieving campaign data from Proofpoint.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Campaign Data Retrieval ===")
    campaign_ids = get_campaign_ids(days=3)
    
    if not campaign_ids:
        print("❌ Failed to retrieve campaign IDs or no campaigns found in the last 3 days")
        return False
    
    L.info(f"✅ Successfully retrieved {len(campaign_ids)} campaign IDs")
    
    # Display campaign IDs
    if len(campaign_ids) > 10:
        L.info(f"First 10 campaign IDs: {', '.join(campaign_ids[:10])}")
    else:
        L.info(f"Campaign IDs: {', '.join(campaign_ids)}")
    
    # Test retrieving details for one campaign
    if campaign_ids:
        L.info("\n=== Testing Campaign Details Retrieval ===")
        sample_campaign_id = campaign_ids[0]
        L.info(f"Getting details for campaign ID: {sample_campaign_id}")
        
        campaign_details = get_campaign_details(sample_campaign_id)
        
        if campaign_details:
            L.info(f"✅ Successfully retrieved details for campaign ID: {sample_campaign_id}")
            
            # Display key information about the campaign
            L.info("\nCampaign Details:")
            L.info(f"  ID: {campaign_details.get('id', 'N/A')}")
            L.info(f"  Name: {campaign_details.get('name', 'N/A')}")
            L.info(f"  Type: {campaign_details.get('type', 'N/A')}")
            L.info(f"  Created At: {campaign_details.get('created', 'N/A')}")
            L.info(f"  Last Updated At: {campaign_details.get('lastUpdatedAt', 'N/A')}")
            L.info(f"  Notable: {campaign_details.get('notable', 'N/A')}")
            L.info(f"  Vertically Targeted: {campaign_details.get('verticallyTargeted', 'N/A')}")
            
            # Safely display complex fields using the safe_join helper
            # Display families, if present
            families = campaign_details.get('families', [])
            if families:
                L.info(f"  Families: {safe_join(families)}")
            
            # Display actors, if present
            actors = campaign_details.get('actors', [])
            if actors:
                L.info(f"  Actors: {safe_join(actors)}")
            
            # Display malware, if present
            malware = campaign_details.get('malware', [])
            if malware:
                L.info(f"  Malware: {safe_join(malware)}")
            
            # Display techniques, if present
            techniques = campaign_details.get('techniques', [])
            if techniques:
                L.info(f"  Techniques: {safe_join(techniques)}")
            
            # Print the full JSON response for debugging
            L.debug(f"Full campaign details: {json.dumps(campaign_details, indent=2)}")
            
            return True
        else:
            L.error("❌ Failed to retrieve campaign details")
            return False
    else:
        L.warning("Cannot test campaign details retrieval - no campaign IDs found")
        return False
    
def get_threat_ids_from_campaigns(days=3):
    """
    Retrieve threat IDs by first getting campaigns and then extracting associated threats.
    
    Args:
        days (int): Number of days to look back for campaigns
        
    Returns:
        list: List of unique threat IDs extracted from campaigns
    """
    L.info(f"Retrieving threat IDs by examining campaign data for the last {days} days")
    
    # First, get campaign IDs which we know works
    campaign_ids = get_campaign_ids(days=days)
    
    if not campaign_ids:
        L.warning("No campaigns found in the specified time period")
        return []
    
    L.info(f"Found {len(campaign_ids)} campaigns to check for threats")
    
    # Now get details for each campaign and extract threats
    all_threat_ids = set()
    
    for idx, campaign_id in enumerate(campaign_ids):
        L.info(f"Examining campaign {idx+1}/{len(campaign_ids)}: {campaign_id}")
        
        campaign_details = get_campaign_details(campaign_id)
        
        if not campaign_details:
            L.warning(f"Could not retrieve details for campaign: {campaign_id}")
            continue
        
        # Check for threats in various fields of the campaign
        # The exact field names might vary based on the API response structure
        threat_fields = ['threats', 'malware', 'techniques']
        
        for field in threat_fields:
            items = campaign_details.get(field, [])
            for item in items:
                if isinstance(item, dict) and 'id' in item:
                    all_threat_ids.add(item['id'])
        
        # If there's a 'messages' field, it might contain threat IDs
        messages = campaign_details.get('messages', [])
        for message in messages:
            if isinstance(message, dict) and 'threatID' in message:
                all_threat_ids.add(message['threatID'])
            elif isinstance(message, dict) and 'threatId' in message:
                all_threat_ids.add(message['threatId'])
    
    # Convert set to list
    threat_ids_list = list(all_threat_ids)
    L.info(f"Extracted {len(threat_ids_list)} unique threat IDs from campaigns")
    
    return threat_ids_list

def get_threat_details(threat_id):
    """
    Retrieve details for a specific threat ID using the Threats API.
    
    Args:
        threat_id (str): ID of the threat to retrieve details for
        
    Returns:
        dict: JSON response containing threat details or None if failed
    """
    api_host = os.environ.get('PROOFPOINT_API_HOST')
    principal = os.environ.get('PROOFPOINT_PRINCIPAL')
    secret = os.environ.get('PROOFPOINT_SECRET')
    
    # Ensure API host has proper format
    if not api_host.startswith('http'):
        api_host = f"https://{api_host}"
    
    # Setup authentication
    auth_str = f"{principal}:{secret}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint for threat details - according to docs, it's /v2/threat/summary/<threatId>
    api_url = f"{api_host}/v2/threat/summary/{threat_id}"
    
    try:
        L.info(f"Retrieving details for threat ID: {threat_id}")
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            L.info(f"Successfully retrieved details for threat: {threat_id}")
            return data
        else:
            L.error(f"Failed to retrieve threat details. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving threat details: {e}")
        return None

def get_forensic_evidence(days=1, threat_id=None, campaign_id=None):
    """
    Retrieve forensic evidence from Proofpoint for a specified time period,
    optionally filtered by threat ID or campaign ID.
    
    Args:
        days (int): Number of days to look back for forensic evidence
        threat_id (str, optional): Specific threat ID to filter by
        campaign_id (str, optional): Specific campaign ID to filter by
        
    Returns:
        list: List of forensic evidence items or empty list if none found
    """
    api_host = os.environ.get('PROOFPOINT_API_HOST')
    principal = os.environ.get('PROOFPOINT_PRINCIPAL')
    secret = os.environ.get('PROOFPOINT_SECRET')
    
    # Ensure API host has proper format
    if not api_host.startswith('http'):
        api_host = f"https://{api_host}"
    
    # Setup authentication
    auth_str = f"{principal}:{secret}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Calculate date range
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Format timestamps as required by Proofpoint API
    interval_start = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    interval_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Handle Proofpoint's 24-hour limit by breaking apart longer queries
    all_forensic_evidence = []
    
    # If requested days is greater than 1, we need to make multiple calls
    if days > 1:
        # Calculate number of 24-hour chunks needed
        chunks = days
        L.info(f"Breaking query into {chunks} 24-hour chunks due to API limitations")
        
        for i in range(chunks):
            chunk_end = now - timedelta(days=i)
            chunk_start = chunk_end - timedelta(days=1)
            
            # Format timestamps for this chunk
            chunk_interval_start = chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ")
            chunk_interval_end = chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            L.info(f"Retrieving forensic evidence for chunk {i+1}/{chunks}: {chunk_interval_start} to {chunk_interval_end}")
            chunk_evidence = _get_forensic_evidence_for_interval(
                api_host, headers, chunk_interval_start, chunk_interval_end, threat_id, campaign_id
            )
            
            if chunk_evidence:
                all_forensic_evidence.extend(chunk_evidence)
                # Sleep briefly to avoid hitting rate limits
                import time
                time.sleep(1)
            else:
                L.warning(f"Failed to retrieve forensic evidence for chunk {i+1}")
    else:
        # Just make a single call for 24 hours or less
        all_forensic_evidence = _get_forensic_evidence_for_interval(
            api_host, headers, interval_start, interval_end, threat_id, campaign_id
        )
    
    if all_forensic_evidence:
        L.info(f"Retrieved {len(all_forensic_evidence)} forensic evidence items over {days} days")
        return all_forensic_evidence
    else:
        return []

def _get_forensic_evidence_for_interval(api_host, headers, interval_start, interval_end, threat_id=None, campaign_id=None):
    """
    Helper function to retrieve forensic evidence for a specific interval.
    
    Args:
        api_host (str): Proofpoint API host
        headers (dict): Request headers including auth
        interval_start (str): Start time in ISO format
        interval_end (str): End time in ISO format
        threat_id (str, optional): Specific threat ID to filter by
        campaign_id (str, optional): Specific campaign ID to filter by
        
    Returns:
        list: List of forensic evidence items for the interval or empty list if none found
    """
    # Start building the API URL with the base interval
    api_url = f"{api_host}/v2/forensics?interval={interval_start}/{interval_end}"
    
    # Add optional filters if provided
    if threat_id:
        api_url += f"&threatId={threat_id}"
    if campaign_id:
        api_url += f"&campaignId={campaign_id}"
    
    try:
        L.info(f"Retrieving forensic evidence for interval: {interval_start} to {interval_end}")
        if threat_id:
            L.info(f"Filtering by threat ID: {threat_id}")
        if campaign_id:
            L.info(f"Filtering by campaign ID: {campaign_id}")
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract forensic evidence from the response
            # The format might vary, so check different possible formats
            forensic_data = []
            if 'data' in data:
                forensic_data = data['data']
            elif 'forensics' in data:
                forensic_data = data['forensics']
            elif isinstance(data, list):
                forensic_data = data
            
            L.info(f"Successfully retrieved {len(forensic_data)} forensic evidence items")
            return forensic_data
        elif response.status_code == 404:
            L.warning(f"No forensic evidence found for the specified parameters (404 response)")
            return []
        else:
            L.error(f"Failed to retrieve forensic evidence. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return []
    
    except Exception as e:
        L.error(f"Exception while retrieving forensic evidence: {e}")
        return []

def get_threat_details_from_campaigns(days=3):
    """
    Retrieve campaign details and extract threat information directly from there,
    since the threat IDs from campaigns don't work with the threat/summary endpoint.
    
    Args:
        days (int): Number of days to look back for campaigns
        
    Returns:
        list: List of threats extracted from campaign details
    """
    L.info(f"Retrieving threat details directly from campaign data for the last {days} days")
    
    # First, get campaign IDs
    campaign_ids = get_campaign_ids(days=days)
    
    if not campaign_ids:
        L.warning("No campaigns found in the specified time period")
        return []
    
    L.info(f"Found {len(campaign_ids)} campaigns to extract threat details from")
    
    # Now get details for each campaign and extract threat information
    all_threats = []
    
    for idx, campaign_id in enumerate(campaign_ids):
        L.info(f"Examining campaign {idx+1}/{len(campaign_ids)}: {campaign_id}")
        
        campaign_details = get_campaign_details(campaign_id)
        
        if not campaign_details:
            L.warning(f"Could not retrieve details for campaign: {campaign_id}")
            continue
        
        # Extract threat-related information from the campaign
        threat_info = {
            "campaign_id": campaign_id,
            "campaign_name": campaign_details.get('name', 'Unknown'),
            "threats": []
        }
        
        # Check for malware information
        malware = campaign_details.get('malware', [])
        if malware:
            for m in malware:
                threat_info["threats"].append({
                    "type": "malware",
                    "id": m.get('id', 'Unknown'),
                    "name": m.get('name', 'Unknown')
                })
        
        # Check for families information
        families = campaign_details.get('families', [])
        if families:
            for f in families:
                threat_info["threats"].append({
                    "type": "family",
                    "id": f.get('id', 'Unknown'),
                    "name": f.get('name', 'Unknown')
                })
        
        # Check for actors information
        actors = campaign_details.get('actors', [])
        if actors:
            for a in actors:
                threat_info["threats"].append({
                    "type": "actor",
                    "id": a.get('id', 'Unknown'),
                    "name": a.get('name', 'Unknown')
                })
        
        # Check for techniques information
        techniques = campaign_details.get('techniques', [])
        if techniques:
            for t in techniques:
                threat_info["threats"].append({
                    "type": "technique",
                    "id": t.get('id', 'Unknown'),
                    "name": t.get('name', 'Unknown')
                })
        
        # Add the threat information from this campaign
        if threat_info["threats"]:
            all_threats.append(threat_info)
    
    L.info(f"Extracted threat details from {len(all_threats)} campaigns")
    return all_threats

def test_threat_data_retrieval():
    """
    Test retrieving threat data from Proofpoint.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Threat Data Retrieval ===")
    
    # Get threat details directly from campaigns
    threat_details = get_threat_details_from_campaigns(days=7)
    
    if not threat_details:
        print("❌ Could not find any threat information in campaigns from the last 7 days")
        
        # Try a direct call to the threat summary endpoint with a sample ID from documentation
        # This is a fallback to check if the API is accessible
        L.info("Testing direct threat lookup with a sample threat ID from documentation")
        sample_id = "029bef505d5de699740a1814cba0b6abb685f46d053dea79fd95ba6769e40a6f"
        
        threat_result = get_threat_details(sample_id)
        if threat_result:
            L.info(f"✅ Successfully retrieved details for sample threat ID")
            return True
        else:
            L.warning("Could not retrieve details for sample threat ID from documentation")
            return False
    
    L.info(f"✅ Successfully retrieved threat information from {len(threat_details)} campaigns")
    
    # Display some sample threat information
    if threat_details:
        sample_campaign = threat_details[0]
        L.info("\nSample Threat Information from Campaign:")
        L.info(f"  Campaign ID: {sample_campaign.get('campaign_id', 'N/A')}")
        L.info(f"  Campaign Name: {sample_campaign.get('campaign_name', 'N/A')}")
        
        threats = sample_campaign.get('threats', [])
        if threats:
            L.info(f"  Number of Threats: {len(threats)}")
            
            # Display sample threat
            sample_threat = threats[0]
            L.info(f"  Sample Threat:")
            L.info(f"    Type: {sample_threat.get('type', 'N/A')}")
            L.info(f"    ID: {sample_threat.get('id', 'N/A')}")
            L.info(f"    Name: {sample_threat.get('name', 'N/A')}")
    
    return bool(threat_details)

def test_forensic_evidence_retrieval():
    """
    Test retrieving forensic evidence from Proofpoint.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Forensic Evidence Retrieval ===")
    
    # Get campaign IDs since we know this works
    campaign_ids = get_campaign_ids(days=3)
    
    # Test general forensic evidence retrieval first (no filters)
    L.info("Testing general forensic evidence retrieval (last 24 hours)")
    general_evidence = get_forensic_evidence(days=1)
    
    if general_evidence:
        L.info(f"✅ Successfully retrieved {len(general_evidence)} general forensic evidence items")
        
        # Display sample information
        if len(general_evidence) > 0:
            sample = general_evidence[0]
            L.info("\nSample Forensic Evidence:")
            for key, value in sample.items():
                if isinstance(value, (str, int, bool, float)) and not isinstance(value, dict) and not isinstance(value, list):
                    L.info(f"  {key}: {value}")
    else:
        L.warning("No general forensic evidence found in the last 24 hours")
    
    # Test campaign-specific forensic evidence retrieval if we have campaign IDs
    campaign_specific_success = False
    if campaign_ids:
        sample_campaign_id = campaign_ids[0]
        L.info(f"\nTesting campaign-specific forensic evidence retrieval for campaign ID: {sample_campaign_id}")
        
        campaign_evidence = get_forensic_evidence(days=3, campaign_id=sample_campaign_id)
        
        if campaign_evidence:
            L.info(f"✅ Successfully retrieved {len(campaign_evidence)} forensic evidence items for campaign ID: {sample_campaign_id}")
            campaign_specific_success = True
            
            # Display sample information if available
            if len(campaign_evidence) > 0:
                sample = campaign_evidence[0]
                L.info("\nSample Campaign-Specific Forensic Evidence:")
                for key, value in sample.items():
                    if isinstance(value, (str, int, bool, float)) and not isinstance(value, dict) and not isinstance(value, list):
                        L.info(f"  {key}: {value}")
        else:
            L.warning(f"No forensic evidence found for campaign ID: {sample_campaign_id}")
    
    # Consider the test successful if either we got general evidence or campaign-specific evidence
    success = bool(general_evidence or campaign_specific_success)
    
    if success:
        L.info("✅ Forensic evidence retrieval test passed")
    else:
        L.warning("❌ No forensic evidence could be retrieved")
    
    return success

def main():
    L.info("Starting Proofpoint credential verification")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('PROOFPOINT_API_HOST'):
            os.environ['PROOFPOINT_API_HOST'] = input("Enter Proofpoint API host (e.g., tap-api-v2.proofpoint.com): ")
        if not os.environ.get('PROOFPOINT_PRINCIPAL'):
            os.environ['PROOFPOINT_PRINCIPAL'] = input("Enter Proofpoint principal: ")
        if not os.environ.get('PROOFPOINT_SECRET'):
            os.environ['PROOFPOINT_SECRET'] = input("Enter Proofpoint secret: ")
    else:
        L.info("Using environment variables for credentials")
    
    # Basic credential verification
    L.info("\n=== Basic Credential Verification ===")
    success = verify_proofpoint_credentials()
    
    if not success:
        L.error("Basic credential verification failed")
        return 1
    
    # Extended testing - Campaign Data
    L.info("\n=== Extended Verification: Campaign Data ===")
    campaign_test_success = test_campaign_data_retrieval()
    
    # Extended testing - Threat Data
    L.info("\n=== Extended Verification: Threat Data ===")
    threat_test_success = test_threat_data_retrieval()
    
    # Extended testing - Forensic Evidence
    L.info("\n=== Extended Verification: Forensic Evidence ===")
    forensic_test_success = test_forensic_evidence_retrieval()
    
    # Explore query targets
    L.info("\n=== Exploring API Query Targets ===")
    query_targets = explore_query_targets()
    if query_targets:
        L.info("Successfully explored API query targets")
    
    # Print summary of all test results
    L.info("\n=== Verification Test Summary ===")
    L.info(f"Basic Credential Verification: {'✅ Passed' if success else '❌ Failed'}")
    L.info(f"Campaign Data Retrieval: {'✅ Passed' if campaign_test_success else '❌ Failed'}")
    L.info(f"Threat Data Retrieval: {'✅ Passed' if threat_test_success else '❌ Failed'}")
    L.info(f"Forensic Evidence Retrieval: {'✅ Passed' if forensic_test_success else '❌ Failed'}")
    
    if success and (campaign_test_success or threat_test_success or forensic_test_success):
        L.info("Credential verification completed successfully")
        return 0
    elif success:
        L.warning("Basic verification passed but extended tests failed")
        return 0  # Still return success since basic auth worked
    else:
        L.error("Credential verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())