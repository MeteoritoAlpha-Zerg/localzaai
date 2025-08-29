import os
import sys
import json
import logging
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, ConnectionError

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('guardduty_verification.log')
    ]
)
L = logging.getLogger(__name__)

def verify_guardduty_credentials():
    """
    Verify AWS GuardDuty credentials by attempting to authenticate and access GuardDuty resources.
    
    Environment variables required:
    - AWS_REGION: AWS region (e.g., 'us-east-1')
    - AWS_ACCESS_KEY_ID: AWS Access Key ID
    - AWS_SECRET_ACCESS_KEY: AWS Secret Access Key
    - AWS_SESSION_TOKEN: Optional AWS Session Token for temporary credentials
    
    Returns:
    - True if credentials are valid and can access GuardDuty API
    - False otherwise
    """
    
    # Get environment variables
    region = os.environ.get('AWS_REGION')
    access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    session_token = os.environ.get('AWS_SESSION_TOKEN')
    
    L.info("Retrieved environment variables")
    L.info(f"Using region: {region}")
    
    # Validate that all necessary environment variables are set
    missing_vars = []
    if not region:
        missing_vars.append('AWS_REGION')
    if not access_key_id:
        missing_vars.append('AWS_ACCESS_KEY_ID')
    if not secret_access_key:
        missing_vars.append('AWS_SECRET_ACCESS_KEY')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    try:
        # Create session with credentials
        L.info(f"Attempting to connect to AWS GuardDuty in region: {region}")
        
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=region
        )
        
        # Create GuardDuty client
        guardduty_client = session.client('guardduty')
        
        # Test GuardDuty API with a simple call to list detectors
        L.info("Testing GuardDuty API...")
        response = guardduty_client.list_detectors()
        L.info(f"GuardDuty API test successful. Response: {response}")
        
        # If we get here, authentication was successful
        L.info("Authentication successful")
        
        return True
        
    except ConnectionError as e:
        L.error(f"Connection error: {e}")
        return False
    except ClientError as e:
        L.error(f"AWS Client error: {e}")
        return False
    except Exception as e:
        error_msg = f"Exception occurred while connecting to GuardDuty: {e}"
        L.error(error_msg)
        return False

def get_guardduty_detectors():
    """
    Retrieve a list of GuardDuty detectors in the current region.
    
    Returns:
        list: List of detector information or None if failed
    """
    try:
        # Get environment variables
        region = os.environ.get('AWS_REGION')
        access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        session_token = os.environ.get('AWS_SESSION_TOKEN')
        
        # Create session with credentials
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=region
        )
        
        # Create GuardDuty client
        guardduty_client = session.client('guardduty')
        
        L.info("Retrieving list of GuardDuty detectors...")
        
        # Get detectors
        response = guardduty_client.list_detectors()
        detector_ids = response.get('DetectorIds', [])
        
        if not detector_ids:
            L.warning("No GuardDuty detectors found in the current region")
            return []
        
        detectors_info = []
        for detector_id in detector_ids:
            # Get detector details
            detector = guardduty_client.get_detector(DetectorId=detector_id)
            
            # Get member accounts for this detector
            try:
                members_response = guardduty_client.list_members(DetectorId=detector_id)
                member_count = len(members_response.get('Members', []))
            except Exception as e:
                L.warning(f"Error retrieving members for detector {detector_id}: {e}")
                member_count = 0
            
            # Handle timestamp objects, which may be datetime objects or strings
            created_at = detector.get('CreatedAt')
            updated_at = detector.get('UpdatedAt')
            
            if created_at and not isinstance(created_at, str):
                created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_at_str = str(created_at) if created_at else 'UNKNOWN'
                
            if updated_at and not isinstance(updated_at, str):
                updated_at_str = updated_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                updated_at_str = str(updated_at) if updated_at else 'UNKNOWN'
            
            info = {
                'id': detector_id,
                'status': detector.get('Status', 'UNKNOWN'),
                'finding_publishing_frequency': detector.get('FindingPublishingFrequency', 'UNKNOWN'),
                'service_role': detector.get('ServiceRole', 'UNKNOWN'),
                'data_sources': detector.get('DataSources', {}),
                'member_count': member_count,
                'created_at': created_at_str,
                'updated_at': updated_at_str
            }
            detectors_info.append(info)
            L.info(f"Retrieved information for detector: {detector_id}")
        
        L.info(f"Successfully retrieved information for {len(detectors_info)} detectors")
        return detectors_info
        
    except Exception as e:
        L.error(f"Exception while retrieving detectors: {e}")
        return None

def get_guardduty_findings(detector_id, max_results=10, days_back=30):
    """
    Retrieve GuardDuty findings from a specific detector.
    
    Args:
        detector_id (str): ID of the GuardDuty detector
        max_results (int): Maximum number of findings to retrieve
        days_back (int): Number of days back to retrieve findings from
        
    Returns:
        list: List of findings or None if failed
    """
    try:
        # Get environment variables
        region = os.environ.get('AWS_REGION')
        access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        session_token = os.environ.get('AWS_SESSION_TOKEN')
        
        # Create session with credentials
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=region
        )
        
        # Create GuardDuty client
        guardduty_client = session.client('guardduty')
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        L.info(f"Retrieving findings from detector '{detector_id}' (limit: {max_results}, time range: last {days_back} days)...")
        
        # Create finding criteria
        finding_criteria = {
            'Criterion': {
                'updatedAt': {
                    'Gte': int(start_time.timestamp() * 1000),
                    'Lte': int(end_time.timestamp() * 1000)
                }
            }
        }
        
        # Get findings
        response = guardduty_client.list_findings(
            DetectorId=detector_id,
            FindingCriteria=finding_criteria,
            MaxResults=max_results,
            SortCriteria={
                'AttributeName': 'severity',
                'OrderBy': 'DESC'
            }
        )
        
        finding_ids = response.get('FindingIds', [])
        
        if not finding_ids:
            L.warning(f"No findings found for detector '{detector_id}' in the specified time range")
            return []
        
        # Get detailed information for each finding
        findings_response = guardduty_client.get_findings(
            DetectorId=detector_id,
            FindingIds=finding_ids
        )
        
        findings = findings_response.get('Findings', [])
        
        findings_info = []
        for finding in findings:
            # Fix timestamp handling to avoid str/int division error
            created_at = finding.get('CreatedAt', 0)
            updated_at = finding.get('UpdatedAt', 0)
            
            # Ensure timestamps are numeric before division
            if isinstance(created_at, str):
                try:
                    created_at = float(created_at)
                except ValueError:
                    created_at = 0
                    
            if isinstance(updated_at, str):
                try:
                    updated_at = float(updated_at)
                except ValueError:
                    updated_at = 0
            
            info = {
                'id': finding.get('Id'),
                'title': finding.get('Title'),
                'description': finding.get('Description'),
                'severity': finding.get('Severity'),
                'type': finding.get('Type'),
                'region': finding.get('Region'),
                'account_id': finding.get('AccountId'),
                'resource_type': finding.get('Resource', {}).get('ResourceType') if 'Resource' in finding else None,
                'created_at': datetime.fromtimestamp(created_at / 1000).strftime('%Y-%m-%d %H:%M:%S') if created_at else 'UNKNOWN',
                'updated_at': datetime.fromtimestamp(updated_at / 1000).strftime('%Y-%m-%d %H:%M:%S') if updated_at else 'UNKNOWN'
            }
            findings_info.append(info)
            L.info(f"Retrieved information for finding: {info['id']}")
        
        L.info(f"Successfully retrieved {len(findings_info)} findings from detector '{detector_id}'")
        return findings_info
        
    except Exception as e:
        L.error(f"Exception while retrieving findings from detector '{detector_id}': {e}")
        return None

def get_finding_details(detector_id, finding_id):
    """
    Retrieve detailed information for a specific GuardDuty finding.
    
    Args:
        detector_id (str): ID of the GuardDuty detector
        finding_id (str): ID of the finding to retrieve details for
        
    Returns:
        dict: Finding details or None if failed
    """
    try:
        # Get environment variables
        region = os.environ.get('AWS_REGION')
        access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        session_token = os.environ.get('AWS_SESSION_TOKEN')
        
        # Create session with credentials
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=region
        )
        
        # Create GuardDuty client
        guardduty_client = session.client('guardduty')
        
        L.info(f"Retrieving details for finding '{finding_id}' from detector '{detector_id}'...")
        
        # Get finding details
        response = guardduty_client.get_findings(
            DetectorId=detector_id,
            FindingIds=[finding_id]
        )
        
        findings = response.get('Findings', [])
        
        if not findings:
            L.warning(f"Finding '{finding_id}' not found in detector '{detector_id}'")
            return None
        
        finding = findings[0]
        
        # Fix timestamp handling to avoid str/int division error
        created_at = finding.get('CreatedAt', 0)
        updated_at = finding.get('UpdatedAt', 0)
        
        # Ensure timestamps are numeric before division
        if isinstance(created_at, str):
            try:
                created_at = float(created_at)
            except ValueError:
                created_at = 0
                
        if isinstance(updated_at, str):
            try:
                updated_at = float(updated_at)
            except ValueError:
                updated_at = 0
        
        # Extract relevant details
        details = {
            'id': finding.get('Id'),
            'title': finding.get('Title'),
            'description': finding.get('Description'),
            'severity': finding.get('Severity'),
            'type': finding.get('Type'),
            'region': finding.get('Region'),
            'account_id': finding.get('AccountId'),
            'created_at': datetime.fromtimestamp(created_at / 1000).strftime('%Y-%m-%d %H:%M:%S') if created_at else 'UNKNOWN',
            'updated_at': datetime.fromtimestamp(updated_at / 1000).strftime('%Y-%m-%d %H:%M:%S') if updated_at else 'UNKNOWN',
            'resource': finding.get('Resource', {}),
            'service': finding.get('Service', {}),
            'actor': finding.get('Service', {}).get('Action', {}).get('AwsApiCallAction', {}).get('RemoteIpDetails', {}) if 'Service' in finding else {},
            'recommendations': [
                finding.get('Service', {}).get('Recommendation', {}).get('Text', 'No recommendation provided')
            ] if 'Service' in finding and 'Recommendation' in finding.get('Service', {}) else ['No recommendations provided']
        }
        
        L.info(f"Successfully retrieved details for finding '{finding_id}'")
        return details
        
    except Exception as e:
        L.error(f"Exception while retrieving finding details: {e}")
        return None

def filter_findings_by_severity(detector_id, severity, max_results=10, days_back=30):
    """
    Filter GuardDuty findings by severity level.
    
    Args:
        detector_id (str): ID of the GuardDuty detector
        severity (float or str): Severity threshold (Low: 1.0-3.9, Medium: 4.0-6.9, High: 7.0-8.9)
                                 or level string ('Low', 'Medium', 'High')
        max_results (int): Maximum number of findings to retrieve
        days_back (int): Number of days back to retrieve findings from
        
    Returns:
        list: List of filtered findings or None if failed
    """
    try:
        # Get environment variables
        region = os.environ.get('AWS_REGION')
        access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        session_token = os.environ.get('AWS_SESSION_TOKEN')
        
        # Create session with credentials
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=region
        )
        
        # Create GuardDuty client
        guardduty_client = session.client('guardduty')
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        # Map severity string to range
        severity_ranges = {
            'Low': {'min': 1.0, 'max': 3.9},
            'Medium': {'min': 4.0, 'max': 6.9},
            'High': {'min': 7.0, 'max': 8.9}
        }
        
        # Determine severity range
        if isinstance(severity, str) and severity in severity_ranges:
            min_severity = severity_ranges[severity]['min']
            max_severity = severity_ranges[severity]['max']
            severity_label = severity
        else:
            try:
                severity_value = float(severity)
                if 1.0 <= severity_value <= 3.9:
                    min_severity = 1.0
                    max_severity = 3.9
                    severity_label = 'Low'
                elif 4.0 <= severity_value <= 6.9:
                    min_severity = 4.0
                    max_severity = 6.9
                    severity_label = 'Medium'
                elif 7.0 <= severity_value <= 8.9:
                    min_severity = 7.0
                    max_severity = 8.9
                    severity_label = 'High'
                else:
                    min_severity = 1.0
                    max_severity = 8.9
                    severity_label = 'All'
            except:
                min_severity = 1.0
                max_severity = 8.9
                severity_label = 'All'
        
        L.info(f"Filtering findings from detector '{detector_id}' by severity '{severity_label}' (range: {min_severity}-{max_severity})...")
        
        # Create finding criteria
        finding_criteria = {
            'Criterion': {
                'severity': {
                    'Gte': min_severity,
                    'Lte': max_severity
                },
                'updatedAt': {
                    'Gte': int(start_time.timestamp() * 1000),
                    'Lte': int(end_time.timestamp() * 1000)
                }
            }
        }
        
        # Get findings
        response = guardduty_client.list_findings(
            DetectorId=detector_id,
            FindingCriteria=finding_criteria,
            MaxResults=max_results,
            SortCriteria={
                'AttributeName': 'severity',
                'OrderBy': 'DESC'
            }
        )
        
        finding_ids = response.get('FindingIds', [])
        
        if not finding_ids:
            L.warning(f"No findings with severity '{severity_label}' found for detector '{detector_id}'")
            return []
        
        # Get detailed information for each finding
        findings_response = guardduty_client.get_findings(
            DetectorId=detector_id,
            FindingIds=finding_ids
        )
        
        findings = findings_response.get('Findings', [])
        
        findings_info = []
        for finding in findings:
            # Fix timestamp handling to avoid str/int division error
            created_at = finding.get('CreatedAt', 0)
            updated_at = finding.get('UpdatedAt', 0)
            
            # Ensure timestamps are numeric before division
            if isinstance(created_at, str):
                try:
                    created_at = float(created_at)
                except ValueError:
                    created_at = 0
                    
            if isinstance(updated_at, str):
                try:
                    updated_at = float(updated_at)
                except ValueError:
                    updated_at = 0
            
            info = {
                'id': finding.get('Id'),
                'title': finding.get('Title'),
                'description': finding.get('Description'),
                'severity': finding.get('Severity'),
                'type': finding.get('Type'),
                'region': finding.get('Region'),
                'account_id': finding.get('AccountId'),
                'resource_type': finding.get('Resource', {}).get('ResourceType') if 'Resource' in finding else None,
                'created_at': datetime.fromtimestamp(created_at / 1000).strftime('%Y-%m-%d %H:%M:%S') if created_at else 'UNKNOWN',
                'updated_at': datetime.fromtimestamp(updated_at / 1000).strftime('%Y-%m-%d %H:%M:%S') if updated_at else 'UNKNOWN'
            }
            findings_info.append(info)
            L.info(f"Retrieved information for finding: {info['id']}")
        
        L.info(f"Successfully retrieved {len(findings_info)} findings with severity '{severity_label}' from detector '{detector_id}'")
        return findings_info
        
    except Exception as e:
        L.error(f"Exception while retrieving findings by severity: {e}")
        return None

def test_guardduty_detectors_and_findings():
    """
    Test retrieving detectors and findings from GuardDuty.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Detector Retrieval ===")
    detectors_data = get_guardduty_detectors()
    
    if not detectors_data:
        L.warning("No detectors found or failed to retrieve detectors")
        detectors_available = False
    else:
        L.info(f"✅ Successfully retrieved {len(detectors_data)} detectors")
        
        # Display detector IDs
        detector_ids = [detector.get('id') for detector in detectors_data]
        L.info(f"Detector IDs: {', '.join(detector_ids)}")
        detectors_available = True
    
    # Test retrieving findings if detectors are available
    if detectors_available and detectors_data:
        L.info("\n=== Testing Finding Retrieval ===")
        test_detector = detectors_data[0]['id']
        
        L.info(f"Attempting to retrieve findings from detector '{test_detector}'...")
        findings_data = get_guardduty_findings(test_detector, max_results=5, days_back=30)
        
        if findings_data and len(findings_data) > 0:
            L.info(f"✅ Successfully retrieved {len(findings_data)} findings from detector '{test_detector}'")
            
            # Display finding IDs
            finding_ids = [finding.get('id') for finding in findings_data]
            L.info(f"Finding IDs: {', '.join(finding_ids[:3])}...")
            
            # Test retrieving details of a specific finding
            if finding_ids:
                test_finding = finding_ids[0]
                L.info(f"\n=== Testing Finding Details Retrieval ===")
                L.info(f"Attempting to retrieve details for finding '{test_finding}'...")
                
                finding_details = get_finding_details(test_detector, test_finding)
                
                if finding_details:
                    L.info(f"✅ Successfully retrieved details for finding '{test_finding}'")
                    L.info(f"Finding title: {finding_details.get('title')}")
                    L.info(f"Finding severity: {finding_details.get('severity')}")
                    L.info(f"Finding recommendations: {finding_details.get('recommendations')}")
                else:
                    L.warning(f"Failed to retrieve details for finding '{test_finding}'")
            
            # Test filtering findings by severity
            L.info(f"\n=== Testing Finding Filtering by Severity ===")
            severities = ['Low', 'Medium', 'High']
            for severity in severities:
                L.info(f"Attempting to filter findings by severity '{severity}'...")
                filtered_findings = filter_findings_by_severity(test_detector, severity, max_results=5, days_back=30)
                
                if filtered_findings is not None:
                    L.info(f"✅ Successfully filtered findings by severity '{severity}'")
                    L.info(f"Found {len(filtered_findings)} findings with severity '{severity}'")
                else:
                    L.warning(f"Failed to filter findings by severity '{severity}'")
        else:
            L.warning(f"No findings found for detector '{test_detector}' or failed to retrieve findings")
    
    # Return success if at least detectors are available
    return detectors_available

def main():
    L.info("Starting AWS GuardDuty credential verification")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--set-env':
        L.info("Using manual credential input mode")
        
        if not os.environ.get('AWS_REGION'):
            os.environ['AWS_REGION'] = input("Enter AWS region (e.g., us-east-1): ")
        if not os.environ.get('AWS_ACCESS_KEY_ID'):
            os.environ['AWS_ACCESS_KEY_ID'] = input("Enter AWS Access Key ID: ")
        if not os.environ.get('AWS_SECRET_ACCESS_KEY'):
            os.environ['AWS_SECRET_ACCESS_KEY'] = input("Enter AWS Secret Access Key: ")
        if not os.environ.get('AWS_SESSION_TOKEN'):
            session_token = input("Enter AWS Session Token (optional, press Enter to skip): ")
            if session_token:
                os.environ['AWS_SESSION_TOKEN'] = session_token
    else:
        L.info("Using environment variables for credentials")
    
    # Basic credential verification
    L.info("\n=== Basic Credential Verification ===")
    success = verify_guardduty_credentials()
    
    if not success:
        L.error("Basic credential verification failed")
        return 1
    
    # Extended testing - Detectors and Findings
    L.info("\n=== Extended Verification: Detectors and Findings ===")
    test_success = test_guardduty_detectors_and_findings()
    
    if success and test_success:
        L.info("All credential verification tests completed successfully")
        return 0
    elif success:
        L.warning("Basic verification passed but detector/finding tests found limited or no data")
        return 0  # Still return success since basic auth worked
    else:
        L.error("Credential verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())