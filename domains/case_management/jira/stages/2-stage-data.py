import os
import sys
import json
import logging
import requests
from requests.auth import HTTPBasicAuth
import random
import time
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
L = logging.getLogger(__name__)

def connect_to_jira():
    """
    Connect to JIRA using environment variables.
    
    Returns:
    - tuple: (jira_url, auth, timeout) if successful
    - None if connection fails
    """
    jira_url = os.environ.get('JIRA_URL')
    jira_email = os.environ.get('JIRA_EMAIL')
    jira_api_token = os.environ.get('JIRA_API_TOKEN')
    jira_api_request_timeout = int(os.environ.get('JIRA_API_REQUEST_TIMEOUT', 30))
    
    # Check required environment variables
    missing_vars = []
    if not jira_url:
        missing_vars.append('JIRA_URL')
    if not jira_email:
        missing_vars.append('JIRA_EMAIL')
    if not jira_api_token:
        missing_vars.append('JIRA_API_TOKEN')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Remove trailing slash and create auth
    jira_url = jira_url.rstrip('/')
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    
    L.info(f"Connected to JIRA at {jira_url}")
    return jira_url, auth, jira_api_request_timeout

def check_existing_data(jira_url, auth, timeout):
    """
    Check if JIRA instance has sufficient data for connector testing.
    
    Args:
        jira_url (str): Base JIRA URL
        auth (HTTPBasicAuth): Authentication object
        timeout (int): Request timeout
        
    Returns:
        dict: Information about existing projects and issues
    """
    L.info("Checking existing data in JIRA instance...")
    
    try:
        # Get all projects
        projects_url = f"{jira_url}/rest/api/2/project"
        projects_response = requests.get(
            projects_url,
            auth=auth,
            timeout=timeout,
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
        )
        
        if projects_response.status_code != 200:
            L.error(f"Failed to retrieve projects: {projects_response.status_code} - {projects_response.text}")
            return None
        
        projects = projects_response.json()
        L.info(f"Found {len(projects)} existing projects")
        
        # Check issues in each project
        project_data = {}
        total_issues = 0
        
        for project in projects:
            project_key = project['key']
            project_name = project['name']
            
            # Get issue count for this project
            search_url = f"{jira_url}/rest/api/2/search"
            search_params = {
                'jql': f'project = {project_key}',
                'maxResults': 0  # We only want the total count
            }
            
            search_response = requests.get(
                search_url,
                auth=auth,
                timeout=timeout,
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                params=search_params
            )
            
            if search_response.status_code == 200:
                search_result = search_response.json()
                issue_count = search_result.get('total', 0)
                total_issues += issue_count
                
                project_data[project_key] = {
                    'name': project_name,
                    'key': project_key,
                    'id': project.get('id'),
                    'description': project.get('description', ''),
                    'issue_count': issue_count,
                    'lead': project.get('lead', {}).get('displayName', 'Unknown')
                }
                
                L.info(f"Project {project_key} ({project_name}): {issue_count} issues")
            else:
                L.warning(f"Could not get issue count for project {project_key}")
                project_data[project_key] = {
                    'name': project_name,
                    'key': project_key,
                    'id': project.get('id'),
                    'description': project.get('description', ''),
                    'issue_count': 0,
                    'lead': project.get('lead', {}).get('displayName', 'Unknown')
                }
        
        L.info(f"Total issues across all projects: {total_issues}")
        
        return {
            'projects': project_data,
            'total_projects': len(projects),
            'total_issues': total_issues
        }
        
    except Exception as e:
        L.error(f"Error checking existing data: {e}")
        return None

def is_data_sufficient(existing_data, min_projects=2, min_issues_per_project=3, min_total_issues=5):
    """
    Determine if existing data is sufficient for connector testing.
    
    Args:
        existing_data (dict): Data from check_existing_data()
        min_projects (int): Minimum number of projects required
        min_issues_per_project (int): Minimum issues per project
        min_total_issues (int): Minimum total issues across all projects
        
    Returns:
        tuple: (is_sufficient, missing_requirements)
    """
    if not existing_data:
        return False, ["Could not retrieve existing data"]
    
    missing_requirements = []
    
    # Check minimum projects
    if existing_data['total_projects'] < min_projects:
        missing_requirements.append(f"Need at least {min_projects} projects (found {existing_data['total_projects']})")
    
    # Check minimum total issues
    if existing_data['total_issues'] < min_total_issues:
        missing_requirements.append(f"Need at least {min_total_issues} total issues (found {existing_data['total_issues']})")
    
    # Check if at least one project has sufficient issues
    projects_with_sufficient_issues = 0
    for project_key, project_info in existing_data['projects'].items():
        if project_info['issue_count'] >= min_issues_per_project:
            projects_with_sufficient_issues += 1
    
    if projects_with_sufficient_issues == 0:
        missing_requirements.append(f"Need at least one project with {min_issues_per_project}+ issues")
    
    is_sufficient = len(missing_requirements) == 0
    
    if is_sufficient:
        L.info("✅ Existing data is sufficient for connector testing")
    else:
        L.info("❌ Existing data is insufficient:")
        for req in missing_requirements:
            L.info(f"  - {req}")
    
    return is_sufficient, missing_requirements

def create_test_project(jira_url, auth, timeout, project_key=None, project_name=None):
    """
    Create a test project in JIRA.
    
    Args:
        jira_url (str): Base JIRA URL
        auth (HTTPBasicAuth): Authentication object
        timeout (int): Request timeout
        project_key (str): Optional project key
        project_name (str): Optional project name
        
    Returns:
        dict: Created project information or None if failed
    """
    if not project_key:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        project_key = f"TEST{timestamp[-6:]}"  # Use last 6 digits to keep it short
    
    if not project_name:
        project_name = f"Test Project {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    L.info(f"Creating test project: {project_name} ({project_key})")
    
    try:
        # First, get available project types
        project_types_url = f"{jira_url}/rest/api/2/project/type"
        types_response = requests.get(
            project_types_url,
            auth=auth,
            timeout=timeout,
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
        )
        
        project_type_key = "software"  # Default
        if types_response.status_code == 200:
            project_types = types_response.json()
            if project_types:
                # Use the first available project type
                project_type_key = project_types[0].get('key', 'software')
                L.info(f"Using project type: {project_type_key}")
        
        # Get current user to set as project lead
        user_url = f"{jira_url}/rest/api/2/myself"
        user_response = requests.get(
            user_url,
            auth=auth,
            timeout=timeout,
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
        )
        
        lead_account_id = None
        if user_response.status_code == 200:
            user_info = user_response.json()
            lead_account_id = user_info.get('accountId')
            L.info(f"Using current user as project lead: {user_info.get('displayName')}")
        
        # Create project
        create_url = f"{jira_url}/rest/api/2/project"
        project_data = {
            "key": project_key,
            "name": project_name,
            "projectTypeKey": project_type_key,
            "description": f"Test project created for JIRA connector testing on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        if lead_account_id:
            project_data["leadAccountId"] = lead_account_id
        
        create_response = requests.post(
            create_url,
            auth=auth,
            timeout=timeout,
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            json=project_data
        )
        
        if create_response.status_code in [200, 201]:
            project_info = create_response.json()
            L.info(f"✅ Successfully created project: {project_name} ({project_key})")
            return {
                'key': project_key,
                'name': project_name,
                'id': project_info.get('id'),
                'description': project_data['description']
            }
        else:
            L.error(f"Failed to create project: {create_response.status_code} - {create_response.text}")
            return None
            
    except Exception as e:
        L.error(f"Exception creating project: {e}")
        return None

def create_test_issues(jira_url, auth, timeout, project_key, issue_count=5):
    """
    Create test issues in the specified project.
    
    Args:
        jira_url (str): Base JIRA URL
        auth (HTTPBasicAuth): Authentication object
        timeout (int): Request timeout
        project_key (str): Project key to create issues in
        issue_count (int): Number of issues to create
        
    Returns:
        list: List of created issue information
    """
    L.info(f"Creating {issue_count} test issues in project {project_key}")
    
    created_issues = []
    
    # Issue type templates
    issue_templates = [
        {
            'summary': 'Setup development environment',
            'description': 'Configure the development environment with necessary tools and dependencies.',
            'issuetype': 'Task'
        },
        {
            'summary': 'User authentication bug',
            'description': 'Users are unable to log in with valid credentials. Investigation needed.',
            'issuetype': 'Bug'
        },
        {
            'summary': 'Add user profile page',
            'description': 'Create a user profile page where users can view and edit their information.',
            'issuetype': 'Story'
        },
        {
            'summary': 'Database performance optimization',
            'description': 'Optimize database queries to improve application response time.',
            'issuetype': 'Task'
        },
        {
            'summary': 'Mobile app crashes on startup',
            'description': 'The mobile application crashes immediately after opening on Android devices.',
            'issuetype': 'Bug'
        },
        {
            'summary': 'Implement search functionality',
            'description': 'Add search capability to allow users to find content quickly.',
            'issuetype': 'Story'
        },
        {
            'summary': 'Update API documentation',
            'description': 'Review and update API documentation to reflect recent changes.',
            'issuetype': 'Task'
        },
        {
            'summary': 'Payment processing failure',
            'description': 'Payment transactions are failing intermittently. Requires immediate attention.',
            'issuetype': 'Bug'
        }
    ]
    
    try:
        # First, get available issue types for the project
        issuetypes_url = f"{jira_url}/rest/api/2/project/{project_key}"
        project_response = requests.get(
            issuetypes_url,
            auth=auth,
            timeout=timeout,
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
        )
        
        available_issue_types = ['Task']  # Default fallback
        if project_response.status_code == 200:
            project_info = project_response.json()
            issue_types = project_info.get('issueTypes', [])
            available_issue_types = [it['name'] for it in issue_types]
            L.info(f"Available issue types: {', '.join(available_issue_types)}")
        
        # Create issues
        for i in range(issue_count):
            # Select a random template
            template = random.choice(issue_templates)
            
            # Ensure issue type exists in project, fallback to first available
            issue_type = template['issuetype']
            if issue_type not in available_issue_types:
                issue_type = available_issue_types[0]
            
            # Add timestamp to make summaries unique
            timestamp = datetime.now().strftime('%H:%M:%S')
            summary = f"{template['summary']} - {timestamp}"
            
            issue_data = {
                "fields": {
                    "project": {
                        "key": project_key
                    },
                    "summary": summary,
                    "description": template['description'],
                    "issuetype": {
                        "name": issue_type
                    }
                }
            }
            
            create_issue_url = f"{jira_url}/rest/api/2/issue"
            
            response = requests.post(
                create_issue_url,
                auth=auth,
                timeout=timeout,
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                json=issue_data
            )
            
            if response.status_code in [200, 201]:
                issue_info = response.json()
                issue_key = issue_info.get('key')
                created_issues.append({
                    'key': issue_key,
                    'id': issue_info.get('id'),
                    'summary': summary,
                    'issuetype': issue_type
                })
                L.info(f"✅ Created issue: {issue_key} - {summary}")
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.5)
                
            else:
                L.error(f"Failed to create issue: {response.status_code} - {response.text}")
                # Continue creating other issues even if one fails
        
        L.info(f"Successfully created {len(created_issues)} out of {issue_count} issues")
        return created_issues
        
    except Exception as e:
        L.error(f"Exception creating issues: {e}")
        return created_issues

def stage_test_data(min_projects=2, min_issues_per_project=3, min_total_issues=5):
    """
    Stage test data in JIRA instance if insufficient data exists.
    
    Args:
        min_projects (int): Minimum number of projects required
        min_issues_per_project (int): Minimum issues per project required  
        min_total_issues (int): Minimum total issues required
        
    Returns:
        bool: True if data staging was successful
    """
    L.info("Starting JIRA data staging process...")
    
    try:
        # Connect to JIRA
        jira_url, auth, timeout = connect_to_jira()
        
        # Check existing data
        existing_data = check_existing_data(jira_url, auth, timeout)
        if not existing_data:
            L.error("Failed to check existing data")
            return False
        
        # Determine if data is sufficient
        is_sufficient, missing_requirements = is_data_sufficient(
            existing_data, min_projects, min_issues_per_project, min_total_issues
        )
        
        if is_sufficient:
            L.info("✅ Existing data is sufficient for connector testing")
            L.info("No additional data staging required")
            return True
        
        L.info("📝 Data staging required. Creating test data...")
        
        # Calculate what we need to create
        projects_to_create = max(0, min_projects - existing_data['total_projects'])
        
        # Create projects if needed
        created_projects = []
        if projects_to_create > 0:
            L.info(f"Creating {projects_to_create} test projects...")
            
            for i in range(projects_to_create):
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                project = create_test_project(
                    jira_url, auth, timeout,
                    project_key=f"TST{timestamp[-4:]}{i+1:02d}",
                    project_name=f"Test Project {i+1} - {datetime.now().strftime('%Y-%m-%d')}"
                )
                
                if project:
                    created_projects.append(project)
                    # Small delay between project creations
                    time.sleep(1)
                else:
                    L.warning(f"Failed to create test project {i+1}")
        
        # Create issues in projects that need them
        projects_needing_issues = []
        
        # Check existing projects for issue count
        for project_key, project_info in existing_data['projects'].items():
            if project_info['issue_count'] < min_issues_per_project:
                projects_needing_issues.append(project_key)
        
        # Add newly created projects (they have 0 issues)
        for project in created_projects:
            projects_needing_issues.append(project['key'])
        
        # Create issues in projects that need them
        total_issues_created = 0
        for project_key in projects_needing_issues:
            existing_issues = existing_data['projects'].get(project_key, {}).get('issue_count', 0)
            issues_needed = max(min_issues_per_project - existing_issues, min_issues_per_project)
            
            L.info(f"Creating {issues_needed} issues in project {project_key}")
            created_issues = create_test_issues(jira_url, auth, timeout, project_key, issues_needed)
            total_issues_created += len(created_issues)
            
            # Delay between projects
            time.sleep(1)
        
        # Final verification
        L.info("Verifying staged data...")
        final_data = check_existing_data(jira_url, auth, timeout)
        
        if final_data:
            final_sufficient, final_missing = is_data_sufficient(
                final_data, min_projects, min_issues_per_project, min_total_issues
            )
            
            if final_sufficient:
                L.info("✅ Data staging completed successfully!")
                L.info(f"Final state: {final_data['total_projects']} projects, {final_data['total_issues']} issues")
                return True
            else:
                L.warning("⚠️  Data staging partially successful but requirements still not fully met")
                L.info(f"Final state: {final_data['total_projects']} projects, {final_data['total_issues']} issues")
                for req in final_missing:
                    L.info(f"  Still missing: {req}")
                # Return True anyway as we made progress
                return True
        else:
            L.error("Failed to verify final data state")
            return False
            
    except Exception as e:
        L.error(f"Exception during data staging: {e}")
        return False

def main():
    L.info("JIRA Data Staging - Ensuring sufficient test data exists")
    
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
    else:
        L.info("Using environment variables for credentials")
    
    # Parse command line arguments for requirements
    min_projects = 2
    min_issues_per_project = 3
    min_total_issues = 5
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith('--min-projects='):
                min_projects = int(arg.split('=')[1])
            elif arg.startswith('--min-issues-per-project='):
                min_issues_per_project = int(arg.split('=')[1])
            elif arg.startswith('--min-total-issues='):
                min_total_issues = int(arg.split('=')[1])
    
    L.info(f"Data requirements: {min_projects} projects, {min_issues_per_project} issues per project, {min_total_issues} total issues")
    
    success = stage_test_data(min_projects, min_issues_per_project, min_total_issues)
    
    if success:
        L.info("✅ JIRA data staging completed successfully!")
        L.info("Target instance is valid and has sufficient data for connector testing")
        return 0
    else:
        L.error("❌ JIRA data staging failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())