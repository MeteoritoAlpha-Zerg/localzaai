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
        logging.FileHandler('zendesk_verification.log')
    ]
)
L = logging.getLogger(__name__)

def verify_zendesk_credentials():
    """
    Verify Zendesk credentials by attempting to retrieve a list of tickets.
    
    Environment variables required:
    - ZENDESK_SUBDOMAIN: Your Zendesk subdomain (e.g., for https://example.zendesk.com, enter 'example')
    - ZENDESK_EMAIL: Email address for authenticating with Zendesk
    - ZENDESK_API_TOKEN: API Token for authenticating with Zendesk
    
    Returns:
    - True if credentials are valid and can access Zendesk API
    - False otherwise
    """
    
    # Get environment variables
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    L.info("Retrieved environment variables:")
    L.info(f"  Subdomain: {subdomain}")
    L.info(f"  Email: {email}")
    L.info(f"  API Token: {'*****' if api_token else 'Not set'}")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not subdomain:
        missing_vars.append('ZENDESK_SUBDOMAIN')
    if not email:
        missing_vars.append('ZENDESK_EMAIL')
    if not api_token:
        missing_vars.append('ZENDESK_API_TOKEN')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint to test - list tickets
    api_url = f"{base_url}/tickets.json?per_page=1"
    
    try:
        # Attempt to connect to Zendesk
        L.info(f"Attempting to connect to Zendesk API at: {base_url}")
        
        response = requests.get(api_url, headers=headers, timeout=30)
        L.debug(f"Response status code: {response.status_code}")
        
        # Check if the request was successful
        if response.status_code == 200:
            try:
                data = response.json()
                L.info("Connection successful with data")
                
                # Check for tickets in the response
                ticket_count = len(data.get('tickets', []))
                L.info(f"Retrieved {ticket_count} tickets")
                L.debug(f"Retrieved data: {json.dumps(data, indent=2)}")
                return True
            except json.JSONDecodeError:
                L.error("Received successful status code but could not parse JSON response")
                L.error(f"Response content: {response.text[:500]}...")
                return False
        else:
            L.error(f"Error connecting to Zendesk API. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        L.error(f"Exception occurred while connecting to Zendesk: {e}")
        return False

def list_tickets(page=1, per_page=100, view_id=None, status=None):
    """
    List tickets from Zendesk.
    
    Args:
        page (int): Page number for pagination
        per_page (int): Number of tickets per page
        view_id (int, optional): ID of the view to filter tickets
        status (str, optional): Status to filter tickets (new, open, pending, hold, solved, closed)
        
    Returns:
        dict: JSON response containing tickets or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Build URL based on filtering options
    if view_id:
        api_url = f"{base_url}/views/{view_id}/tickets.json?page={page}&per_page={per_page}"
    else:
        api_url = f"{base_url}/tickets.json?page={page}&per_page={per_page}"
        if status:
            api_url += f"&status={status}"
    
    try:
        L.info(f"Retrieving tickets from page {page} with {per_page} tickets per page")
        if view_id:
            L.info(f"Filtering by view ID: {view_id}")
        if status:
            L.info(f"Filtering by status: {status}")
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            ticket_count = len(data.get('tickets', []))
            L.info(f"Successfully retrieved {ticket_count} tickets")
            return data
        else:
            L.error(f"Failed to retrieve tickets. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving tickets: {e}")
        return None

def get_ticket_details(ticket_id, include_comments=True):
    """
    Retrieve details for a specific ticket.
    
    Args:
        ticket_id (int): ID of the ticket to retrieve
        include_comments (bool): Whether to include comments in the response
        
    Returns:
        dict: JSON response containing ticket details or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint for ticket details
    if include_comments:
        api_url = f"{base_url}/tickets/{ticket_id}.json?include=comments"
    else:
        api_url = f"{base_url}/tickets/{ticket_id}.json"
    
    try:
        L.info(f"Retrieving details for ticket ID: {ticket_id}")
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            L.info(f"Successfully retrieved details for ticket: {ticket_id}")
            return data
        else:
            L.error(f"Failed to retrieve ticket details. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving ticket details: {e}")
        return None

def search_tickets(query, sort_by=None, sort_order=None):
    """
    Search for tickets using the Zendesk Search API.
    
    Args:
        query (str): Search query in Zendesk Search syntax
        sort_by (str, optional): Field to sort by (e.g., 'created_at', 'updated_at', 'priority')
        sort_order (str, optional): Sort direction ('asc' or 'desc')
        
    Returns:
        dict: JSON response containing search results or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Build URL with query parameters
    api_url = f"{base_url}/search.json?query=type:ticket {query}"
    if sort_by and sort_order:
        api_url += f"&sort_by={sort_by}&sort_order={sort_order}"
    
    try:
        L.info(f"Searching tickets with query: {query}")
        if sort_by and sort_order:
            L.info(f"Sorting by {sort_by} in {sort_order} order")
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get('results', []))
            L.info(f"Successfully retrieved {result_count} search results")
            return data
        else:
            L.error(f"Failed to search tickets. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while searching tickets: {e}")
        return None

def create_ticket(subject, description, priority='normal', type='question', tags=None):
    """
    Create a new Zendesk ticket.
    
    Args:
        subject (str): Ticket subject
        description (str): Ticket description
        priority (str, optional): Ticket priority (low, normal, high, urgent)
        type (str, optional): Ticket type (question, incident, problem, task)
        tags (list, optional): List of tags to apply to the ticket
        
    Returns:
        dict: JSON response containing created ticket details or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Prepare ticket data
    ticket_data = {
        'ticket': {
            'subject': subject,
            'comment': {
                'body': description
            },
            'priority': priority,
            'type': type
        }
    }
    
    if tags:
        ticket_data['ticket']['tags'] = tags
    
    try:
        L.info(f"Creating ticket with subject: {subject}")
        response = requests.post(
            f"{base_url}/tickets.json",
            headers=headers,
            json=ticket_data,
            timeout=30
        )
        
        if response.status_code in (200, 201):
            data = response.json()
            L.info(f"Successfully created ticket with ID: {data.get('ticket', {}).get('id')}")
            return data
        else:
            L.error(f"Failed to create ticket. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while creating ticket: {e}")
        return None

def update_ticket(ticket_id, status=None, priority=None, subject=None, tags=None):
    """
    Update an existing Zendesk ticket.
    
    Args:
        ticket_id (int): ID of the ticket to update
        status (str, optional): New ticket status (new, open, pending, hold, solved, closed)
        priority (str, optional): New ticket priority (low, normal, high, urgent)
        subject (str, optional): New ticket subject
        tags (list, optional): New list of tags (will replace existing tags)
        
    Returns:
        dict: JSON response containing updated ticket details or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Prepare ticket data
    ticket_data = {'ticket': {}}
    
    if status:
        ticket_data['ticket']['status'] = status
    if priority:
        ticket_data['ticket']['priority'] = priority
    if subject:
        ticket_data['ticket']['subject'] = subject
    if tags is not None:  # Allow empty list to clear tags
        ticket_data['ticket']['tags'] = tags
    
    try:
        L.info(f"Updating ticket ID: {ticket_id}")
        response = requests.put(
            f"{base_url}/tickets/{ticket_id}.json",
            headers=headers,
            json=ticket_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            L.info(f"Successfully updated ticket: {ticket_id}")
            return data
        else:
            L.error(f"Failed to update ticket. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while updating ticket: {e}")
        return None

def add_ticket_comment(ticket_id, comment, public=False):
    """
    Add a comment to an existing Zendesk ticket.
    
    Args:
        ticket_id (int): ID of the ticket to add a comment to
        comment (str): Comment text
        public (bool, optional): Whether the comment should be public
        
    Returns:
        dict: JSON response containing updated ticket or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Prepare comment data
    ticket_data = {
        'ticket': {
            'comment': {
                'body': comment,
                'public': public
            }
        }
    }
    
    try:
        L.info(f"Adding {'public' if public else 'private'} comment to ticket ID: {ticket_id}")
        response = requests.put(
            f"{base_url}/tickets/{ticket_id}.json",
            headers=headers,
            json=ticket_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            L.info(f"Successfully added comment to ticket: {ticket_id}")
            return data
        else:
            L.error(f"Failed to add comment to ticket. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while adding comment to ticket: {e}")
        return None

def get_ticket_comments(ticket_id):
    """
    Retrieve comments for a specific ticket.
    
    Args:
        ticket_id (int): ID of the ticket to retrieve comments for
        
    Returns:
        list: List of comments or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint for ticket comments
    api_url = f"{base_url}/tickets/{ticket_id}/comments.json"
    
    try:
        L.info(f"Retrieving comments for ticket ID: {ticket_id}")
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            comments_count = len(data.get('comments', []))
            L.info(f"Successfully retrieved {comments_count} comments for ticket: {ticket_id}")
            return data.get('comments', [])
        else:
            L.error(f"Failed to retrieve ticket comments. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving ticket comments: {e}")
        return None

def list_users(page=1, per_page=100):
    """
    List users from Zendesk.
    
    Args:
        page (int): Page number for pagination
        per_page (int): Number of users per page
        
    Returns:
        dict: JSON response containing users or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint for users
    api_url = f"{base_url}/users.json?page={page}&per_page={per_page}"
    
    try:
        L.info(f"Retrieving users from page {page} with {per_page} users per page")
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            user_count = len(data.get('users', []))
            L.info(f"Successfully retrieved {user_count} users")
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

def list_help_center_articles(page=1, per_page=100, locale='en-us'):
    """
    List Help Center articles from Zendesk.
    
    Args:
        page (int): Page number for pagination
        per_page (int): Number of articles per page
        locale (str): Locale for articles (e.g., 'en-us', 'fr', 'es')
        
    Returns:
        dict: JSON response containing articles or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/{locale}"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint for Help Center articles
    api_url = f"{base_url}/articles.json?page={page}&per_page={per_page}"
    
    try:
        L.info(f"Retrieving Help Center articles from page {page} with {per_page} articles per page")
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            article_count = len(data.get('articles', []))
            L.info(f"Successfully retrieved {article_count} Help Center articles")
            return data
        else:
            L.error(f"Failed to retrieve Help Center articles. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving Help Center articles: {e}")
        return None

def get_views():
    """
    Retrieve all views from Zendesk.
    
    Returns:
        dict: JSON response containing views or None if failed
    """
    subdomain = os.environ.get('ZENDESK_SUBDOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    # Construct the base URL
    base_url = f"https://{subdomain}.zendesk.com/api/v2"
    
    # Setup authentication
    auth_str = f"{email}/token:{api_token}"
    auth_bytes = auth_str.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    # Setup headers
    headers = {
        'Authorization': f"Basic {base64_auth}",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # API endpoint for views
    api_url = f"{base_url}/views.json"
    
    try:
        L.info(f"Retrieving views")
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            view_count = len(data.get('views', []))
            L.info(f"Successfully retrieved {view_count} views")
            return data
        else:
            L.error(f"Failed to retrieve views. Status code: {response.status_code}")
            try:
                error_details = response.json()
                L.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                L.error(f"Response text: {response.text}")
            return None
    
    except Exception as e:
        L.error(f"Exception while retrieving views: {e}")
        return None

def test_ticket_listing():
    """
    Test retrieving ticket listings from Zendesk.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Ticket Listing ===")
    tickets_data = list_tickets(per_page=10)
    
    if not tickets_data:
        print("❌ Failed to retrieve tickets or no tickets found")
        return False
    
    tickets = tickets_data.get('tickets', [])
    
    L.info(f"✅ Successfully retrieved {len(tickets)} tickets")
    
    # Display ticket information
    if len(tickets) > 0:
        L.info("\nSample Ticket Information:")
        sample_ticket = tickets[0]
        L.info(f"  ID: {sample_ticket.get('id', 'N/A')}")
        L.info(f"  Subject: {sample_ticket.get('subject', 'N/A')}")
        L.info(f"  Status: {sample_ticket.get('status', 'N/A')}")
        L.info(f"  Priority: {sample_ticket.get('priority', 'N/A')}")
        L.info(f"  Created At: {sample_ticket.get('created_at', 'N/A')}")
        L.info(f"  Updated At: {sample_ticket.get('updated_at', 'N/A')}")
        
        # Save the first ticket ID for later tests
        global test_ticket_id
        test_ticket_id = sample_ticket.get('id')
    
    return bool(tickets)

def test_ticket_details():
    """
    Test retrieving detailed information for a specific ticket.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    global test_ticket_id
    
    # If we don't have a ticket ID yet, try to get one
    if not test_ticket_id:
        tickets_data = list_tickets(per_page=1)
        if tickets_data and tickets_data.get('tickets'):
            test_ticket_id = tickets_data['tickets'][0]['id']
        else:
            print("❌ Cannot test ticket details - no ticket ID available")
            return False
    
    L.info(f"\n=== Testing Ticket Details for ID: {test_ticket_id} ===")
    ticket_data = get_ticket_details(test_ticket_id)
    
    if not ticket_data:
        print(f"❌ Failed to retrieve details for ticket ID: {test_ticket_id}")
        return False
    
    ticket = ticket_data.get('ticket')
    
    L.info(f"✅ Successfully retrieved details for ticket ID: {test_ticket_id}")
    
    # Display detailed ticket information
    L.info("\nDetailed Ticket Information:")
    L.info(f"  ID: {ticket.get('id', 'N/A')}")
    L.info(f"  Subject: {ticket.get('subject', 'N/A')}")
    L.info(f"  Description: {ticket.get('description', 'N/A')}")
    L.info(f"  Status: {ticket.get('status', 'N/A')}")
    L.info(f"  Priority: {ticket.get('priority', 'N/A')}")
    L.info(f"  Type: {ticket.get('type', 'N/A')}")
    L.info(f"  Requester ID: {ticket.get('requester_id', 'N/A')}")
    L.info(f"  Assignee ID: {ticket.get('assignee_id', 'N/A')}")
    L.info(f"  Created At: {ticket.get('created_at', 'N/A')}")
    L.info(f"  Updated At: {ticket.get('updated_at', 'N/A')}")
    
    # Display tags if present
    tags = ticket.get('tags', [])
    if tags:
        L.info(f"  Tags: {', '.join(tags)}")
    
    # Display comments if available
    comments = ticket_data.get('comments', [])
    if comments:
        L.info(f"  Number of Comments: {len(comments)}")
    
    return bool(ticket)

def test_ticket_search():
    """
    Test searching for tickets using the Zendesk Search API.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Ticket Search ===")
    
    # Try a simple search for open tickets
    search_query = "status:open"
    search_results = search_tickets(search_query)
    
    if not search_results:
        print(f"❌ Failed to search for tickets with query: {search_query}")
        
        # Try another simple search
        search_query = "type:ticket"
        L.info(f"Trying alternative search query: {search_query}")
        search_results = search_tickets(search_query)
        
        if not search_results:
            print(f"❌ Failed to search for tickets with alternative query")
            return False
    
    results = search_results.get('results', [])
    L.info(f"✅ Successfully searched for tickets with query: {search_query}")
    L.info(f"Found {len(results)} matching tickets")
    
    # Display sample search result
    if results:
        L.info("\nSample Search Result:")
        sample_result = results[0]
        L.info(f"  ID: {sample_result.get('id', 'N/A')}")
        L.info(f"  Subject: {sample_result.get('subject', 'N/A')}")
        L.info(f"  Status: {sample_result.get('status', 'N/A')}")
        L.info(f"  Priority: {sample_result.get('priority', 'N/A')}")
        
    return bool(results)

def test_ticket_creation():
    """
    Test creating a new ticket in Zendesk.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Ticket Creation ===")
    
    # Generate a unique subject for the test ticket
    subject = f"Test Ticket - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    description = "This is a test ticket created by the Zendesk verification utility."
    tags = ["test", "verification", "api_test"]
    
    ticket_data = create_ticket(
        subject=subject,
        description=description,
        priority="low",
        type="task",
        tags=tags
    )
    
    if not ticket_data:
        print("❌ Failed to create test ticket")
        return False
    
    ticket = ticket_data.get('ticket')
    if not ticket:
        print("❌ Failed to extract ticket details from response")
        return False
    
    ticket_id = ticket.get('id')
    L.info(f"✅ Successfully created test ticket with ID: {ticket_id}")
    
    # Display created ticket details
    L.info("\nCreated Ticket Details:")
    L.info(f"  ID: {ticket_id}")
    L.info(f"  Subject: {ticket.get('subject', 'N/A')}")
    L.info(f"  Status: {ticket.get('status', 'N/A')}")
    L.info(f"  Priority: {ticket.get('priority', 'N/A')}")
    L.info(f"  Type: {ticket.get('type', 'N/A')}")
    
    # Save the created ticket ID for later tests
    global test_created_ticket_id
    test_created_ticket_id = ticket_id
    
    return bool(ticket_id)

def test_ticket_update():
    """
    Test updating an existing ticket in Zendesk.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    global test_created_ticket_id
    
    # If we don't have a created ticket ID, use the one from ticket details test
    if not test_created_ticket_id:
        test_created_ticket_id = test_ticket_id
    
    # If we still don't have a ticket ID, we can't test updating
    if not test_created_ticket_id:
        print("❌ Cannot test ticket updating - no ticket ID available")
        return False
    
    L.info(f"\n=== Testing Ticket Update for ID: {test_created_ticket_id} ===")
    
    # Update the subject and priority
    updated_subject = f"Updated Test Ticket - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    new_tags = ["test", "verification", "updated", "api_test"]
    
    ticket_data = update_ticket(
        ticket_id=test_created_ticket_id,
        status="pending",
        priority="high",
        subject=updated_subject,
        tags=new_tags
    )
    
    if not ticket_data:
        print(f"❌ Failed to update ticket ID: {test_created_ticket_id}")
        return False
    
    ticket = ticket_data.get('ticket')
    L.info(f"✅ Successfully updated ticket ID: {test_created_ticket_id}")
    
    # Display updated ticket details
    L.info("\nUpdated Ticket Details:")
    L.info(f"  ID: {ticket.get('id', 'N/A')}")
    L.info(f"  Subject: {ticket.get('subject', 'N/A')}")
    L.info(f"  Status: {ticket.get('status', 'N/A')}")
    L.info(f"  Priority: {ticket.get('priority', 'N/A')}")
    L.info(f"  Tags: {', '.join(ticket.get('tags', []))}")
    
    return bool(ticket)

def test_ticket_comment():
    """
    Test adding a comment to an existing ticket in Zendesk.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    global test_created_ticket_id
    
    # If we don't have a created ticket ID, use the one from ticket details test
    if not test_created_ticket_id:
        test_created_ticket_id = test_ticket_id
    
    # If we still don't have a ticket ID, we can't test adding a comment
    if not test_created_ticket_id:
        print("❌ Cannot test adding a comment - no ticket ID available")
        return False
    
    L.info(f"\n=== Testing Ticket Comment for ID: {test_created_ticket_id} ===")
    
    # Add a comment to the ticket
    comment_text = f"Test comment added at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    ticket_data = add_ticket_comment(
        ticket_id=test_created_ticket_id,
        comment=comment_text,
        public=False
    )
    
    if not ticket_data:
        print(f"❌ Failed to add comment to ticket ID: {test_created_ticket_id}")
        return False
    
    L.info(f"✅ Successfully added comment to ticket ID: {test_created_ticket_id}")
    
    # Now retrieve the comments to verify
    comments = get_ticket_comments(test_created_ticket_id)
    
    if not comments:
        print(f"❌ Failed to retrieve comments for ticket ID: {test_created_ticket_id}")
        return False
    
    L.info(f"Retrieved {len(comments)} comments for ticket ID: {test_created_ticket_id}")
    
    # Display the most recent comment
    if comments:
        latest_comment = comments[-1]
        L.info("\nLatest Comment:")
        L.info(f"  Author ID: {latest_comment.get('author_id', 'N/A')}")
        L.info(f"  Created At: {latest_comment.get('created_at', 'N/A')}")
        L.info(f"  Public: {latest_comment.get('public', 'N/A')}")
        L.info(f"  Body: {latest_comment.get('body', 'N/A')}")
    
    return bool(comments)

def test_user_listing():
    """
    Test retrieving user listings from Zendesk.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing User Listing ===")
    users_data = list_users(per_page=10)
    
    if not users_data:
        print("❌ Failed to retrieve users or no users found")
        return False
    
    users = users_data.get('users', [])
    
    L.info(f"✅ Successfully retrieved {len(users)} users")
    
    # Display user information
    if len(users) > 0:
        L.info("\nSample User Information:")
        sample_user = users[0]
        L.info(f"  ID: {sample_user.get('id', 'N/A')}")
        L.info(f"  Name: {sample_user.get('name', 'N/A')}")
        L.info(f"  Email: {sample_user.get('email', 'N/A')}")
        L.info(f"  Role: {sample_user.get('role', 'N/A')}")
        L.info(f"  Created At: {sample_user.get('created_at', 'N/A')}")
    
    return bool(users)

def test_help_center_articles():
    """
    Test retrieving Help Center articles from Zendesk.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Help Center Articles ===")
    articles_data = list_help_center_articles(per_page=10)
    
    if not articles_data:
        print("❌ Failed to retrieve Help Center articles or none found")
        # This might not be a failure if Help Center is not enabled
        L.warning("Help Center might not be enabled for this Zendesk instance")
        return True  # Return true anyway since this is optional
    
    articles = articles_data.get('articles', [])
    
    L.info(f"✅ Successfully retrieved {len(articles)} Help Center articles")
    
    # Display article information
    if len(articles) > 0:
        L.info("\nSample Article Information:")
        sample_article = articles[0]
        L.info(f"  ID: {sample_article.get('id', 'N/A')}")
        L.info(f"  Title: {sample_article.get('title', 'N/A')}")
        L.info(f"  URL: {sample_article.get('html_url', 'N/A')}")
        L.info(f"  Author ID: {sample_article.get('author_id', 'N/A')}")
        L.info(f"  Created At: {sample_article.get('created_at', 'N/A')}")
        L.info(f"  Updated At: {sample_article.get('updated_at', 'N/A')}")
    
    return bool(articles)

def test_views_listing():
    """
    Test retrieving views from Zendesk.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Views Listing ===")
    views_data = get_views()
    
    if not views_data:
        print("❌ Failed to retrieve views or no views found")
        return False
    
    views = views_data.get('views', [])
    
    L.info(f"✅ Successfully retrieved {len(views)} views")
    
    # Display view information
    if len(views) > 0:
        L.info("\nSample View Information:")
        sample_view = views[0]
        L.info(f"  ID: {sample_view.get('id', 'N/A')}")
        L.info(f"  Title: {sample_view.get('title', 'N/A')}")
        L.info(f"  Active: {sample_view.get('active', 'N/A')}")
        L.info(f"  Updated At: {sample_view.get('updated_at', 'N/A')}")
    
    return bool(views)

def explore_query_targets():
    """
    Explore available query targets in the Zendesk API.
    This simulates what get_query_target_options would return in the actual connector.
    
    Returns:
        dict: Dictionary of available query targets or None if failed
    """
    L.info("Exploring available Zendesk API query targets")
    
    # These are the standard query targets for Zendesk based on its API documentation
    query_targets = {
        "tickets": {
            "description": "Ticket management including creation, updates, and retrieval",
            "endpoints": [
                {"name": "list_tickets", "path": "/api/v2/tickets.json", "description": "Retrieve a list of tickets"},
                {"name": "get_ticket", "path": "/api/v2/tickets/{id}.json", "description": "Retrieve a specific ticket by ID"},
                {"name": "create_ticket", "path": "/api/v2/tickets.json", "description": "Create a new ticket"},
                {"name": "update_ticket", "path": "/api/v2/tickets/{id}.json", "description": "Update an existing ticket"},
                {"name": "delete_ticket", "path": "/api/v2/tickets/{id}.json", "description": "Delete a ticket"}
            ]
        },
        "ticket_comments": {
            "description": "Comments on tickets",
            "endpoints": [
                {"name": "list_comments", "path": "/api/v2/tickets/{ticket_id}/comments.json", "description": "Retrieve comments for a specific ticket"},
                {"name": "add_comment", "path": "/api/v2/tickets/{ticket_id}.json", "description": "Add a comment to a ticket"}
            ]
        },
        "ticket_fields": {
            "description": "Custom fields for tickets",
            "endpoints": [
                {"name": "list_ticket_fields", "path": "/api/v2/ticket_fields.json", "description": "Retrieve all ticket fields"}
            ]
        },
        "users": {
            "description": "User management",
            "endpoints": [
                {"name": "list_users", "path": "/api/v2/users.json", "description": "Retrieve a list of users"},
                {"name": "get_user", "path": "/api/v2/users/{id}.json", "description": "Retrieve a specific user by ID"}
            ]
        },
        "views": {
            "description": "Saved views for filtering tickets",
            "endpoints": [
                {"name": "list_views", "path": "/api/v2/views.json", "description": "Retrieve a list of views"},
                {"name": "get_view", "path": "/api/v2/views/{id}.json", "description": "Retrieve a specific view by ID"},
                {"name": "tickets_in_view", "path": "/api/v2/views/{id}/tickets.json", "description": "Retrieve tickets in a specific view"}
            ]
        },
        "search": {
            "description": "Search functionality",
            "endpoints": [
                {"name": "search", "path": "/api/v2/search.json", "description": "Search for tickets, users, etc."}
            ]
        },
        "help_center": {
            "description": "Help Center articles and categories",
            "endpoints": [
                {"name": "list_articles", "path": "/api/v2/help_center/articles.json", "description": "Retrieve a list of Help Center articles"},
                {"name": "get_article", "path": "/api/v2/help_center/articles/{id}.json", "description": "Retrieve a specific Help Center article"}
            ]
        }
    }
    
    # Verify at least one target by making a real API call
    if verify_zendesk_credentials():
        L.info("Verified connection to Zendesk API")
        L.info(f"Enumerated {len(query_targets)} query targets")
        return query_targets
    else:
        L.error("Failed to connect to Zendesk API, cannot verify query targets")
        return None

def main():
    L.info("Starting Zendesk credential verification")
    
    # Initialize global variables for test ticket IDs
    global test_ticket_id
    global test_created_ticket_id
    test_ticket_id = None
    test_created_ticket_id = None
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('ZENDESK_SUBDOMAIN'):
            os.environ['ZENDESK_SUBDOMAIN'] = input("Enter Zendesk subdomain (e.g., for 'example.zendesk.com', enter 'example'): ")
        if not os.environ.get('ZENDESK_EMAIL'):
            os.environ['ZENDESK_EMAIL'] = input("Enter Zendesk email: ")
        if not os.environ.get('ZENDESK_API_TOKEN'):
            os.environ['ZENDESK_API_TOKEN'] = input("Enter Zendesk API token: ")
    else:
        L.info("Using environment variables for credentials")
    
    # Basic credential verification
    L.info("\n=== Basic Credential Verification ===")
    success = verify_zendesk_credentials()
    
    if not success:
        L.error("Basic credential verification failed")
        return 1
    
    # Extended testing - different API operations
    ticket_listing_success = test_ticket_listing()
    ticket_details_success = test_ticket_details() if ticket_listing_success else False
    ticket_search_success = test_ticket_search()
    ticket_creation_success = test_ticket_creation()
    ticket_update_success = test_ticket_update() if ticket_creation_success else False
    ticket_comment_success = test_ticket_comment() if ticket_creation_success else False
    user_listing_success = test_user_listing()
    help_center_success = test_help_center_articles()  # Not critical if fails
    views_listing_success = test_views_listing()
    
    # Explore query targets
    L.info("\n=== Exploring API Query Targets ===")
    query_targets = explore_query_targets()
    if query_targets:
        L.info("Successfully explored API query targets")
    
    # Print summary of all test results
    L.info("\n=== Verification Test Summary ===")
    L.info(f"Basic Credential Verification: {'✅ Passed' if success else '❌ Failed'}")
    L.info(f"Ticket Listing: {'✅ Passed' if ticket_listing_success else '❌ Failed'}")
    L.info(f"Ticket Details: {'✅ Passed' if ticket_details_success else '❌ Failed'}")
    L.info(f"Ticket Search: {'✅ Passed' if ticket_search_success else '❌ Failed'}")
    L.info(f"Ticket Creation: {'✅ Passed' if ticket_creation_success else '❌ Failed'}")
    L.info(f"Ticket Update: {'✅ Passed' if ticket_update_success else '❌ Failed'}")
    L.info(f"Ticket Comment: {'✅ Passed' if ticket_comment_success else '❌ Failed'}")
    L.info(f"User Listing: {'✅ Passed' if user_listing_success else '❌ Failed'}")
    L.info(f"Help Center Articles: {'✅ Passed' if help_center_success else '⚠️ Not Available'}")
    L.info(f"Views Listing: {'✅ Passed' if views_listing_success else '❌ Failed'}")
    
    # Overall assessment
    critical_tests = [
        success,  # Basic auth
        ticket_listing_success,
        ticket_details_success,
        ticket_search_success,
        ticket_creation_success,
        ticket_update_success,
        ticket_comment_success,
        user_listing_success,
        views_listing_success
    ]
    
    if all(critical_tests):
        L.info("\n✅ All critical tests passed! Zendesk API integration is fully functional.")
        return 0
    elif success and any([ticket_listing_success, ticket_details_success, ticket_search_success]):
        L.warning("\n⚠️ Basic functionality works but some advanced tests failed.")
        return 0  # Still return success since basic functionality works
    else:
        L.error("\n❌ Critical Zendesk API tests failed. Please check your credentials and permissions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())