import os
import sys
import json
import logging
import random
import time
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
L = logging.getLogger(__name__)

def connect_to_guardduty():
    """
    Connect to AWS GuardDuty using environment variables.
    """
    region = os.environ.get('AWS_REGION')
    access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    session_token = os.environ.get('AWS_SESSION_TOKEN')
    
    # Check required environment variables
    missing_vars = []
    if not region:
        missing_vars.append('AWS_REGION')
    if not access_key_id:
        missing_vars.append('AWS_ACCESS_KEY_ID')
    if not secret_access_key:
        missing_vars.append('AWS_SECRET_ACCESS_KEY')
    
    if missing_vars:
        L.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Create session with credentials
    session = boto3.Session(
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token,
        region_name=region
    )
    
    # Create GuardDuty client
    guardduty_client = session.client('guardduty')
    
    return guardduty_client

def verify_or_create_detector(guardduty_client):
    """
    Verify if a GuardDuty detector exists, or create one if none exists.
    
    Returns:
        str: Detector ID
    """
    L.info("Checking for existing GuardDuty detectors...")
    
    # List existing detectors
    try:
        response = guardduty_client.list_detectors()
        detector_ids = response.get('DetectorIds', [])
        
        if detector_ids:
            detector_id = detector_ids[0]
            L.info(f"Found existing GuardDuty detector: {detector_id}")
            
            # Check detector status
            detector = guardduty_client.get_detector(DetectorId=detector_id)
            if detector.get('Status') == 'ENABLED':
                L.info(f"Detector {detector_id} is already enabled")
            else:
                L.info(f"Enabling detector {detector_id}...")
                guardduty_client.update_detector(
                    DetectorId=detector_id,
                    Enable=True
                )
                L.info(f"Detector {detector_id} enabled successfully")
            
            return detector_id
        else:
            L.info("No existing GuardDuty detectors found. Creating a new one...")
            
            # Create a new detector with simplified parameters to avoid errors
            response = guardduty_client.create_detector(
                Enable=True,
                FindingPublishingFrequency='FIFTEEN_MINUTES'
            )
            
            detector_id = response.get('DetectorId')
            L.info(f"Created new GuardDuty detector: {detector_id}")
            return detector_id
            
    except Exception as e:
        L.error(f"Error verifying/creating GuardDuty detector: {e}")
        raise

def create_sample_findings(guardduty_client, detector_id, count=10):
    """
    Create sample findings in GuardDuty.
    
    Args:
        guardduty_client: Boto3 GuardDuty client
        detector_id: ID of the GuardDuty detector
        count: Number of sample findings to create
        
    Returns:
        list: List of created finding IDs
    """
    L.info(f"Creating {count} sample findings for detector {detector_id}...")
    
    # Define sample finding types - using only valid ones based on error messages
    finding_types = [
        'Backdoor:EC2/C&CActivity.B',
        'CryptoCurrency:EC2/BitcoinTool.B',
        'Backdoor:EC2/DenialOfService.Tcp',
        'Backdoor:EC2/DenialOfService.UnusualProtocol',
        'PenTest:IAMUser/KaliLinux',
        'Trojan:EC2/BlackholeTraffic',
        'UnauthorizedAccess:EC2/SSHBruteForce',
        'Recon:EC2/PortProbeUnprotectedPort'
    ]
    
    finding_ids = []
    
    for i in range(count):
        # Select a random finding type
        finding_type = random.choice(finding_types)
        
        try:
            # Create the sample finding
            response = guardduty_client.create_sample_findings(
                DetectorId=detector_id,
                FindingTypes=[finding_type]
            )
            L.info(f"Created sample finding of type {finding_type}")
            finding_ids.append(f"sample-finding-{int(time.time())}-{i}")
        except Exception as e:
            L.error(f"Error creating sample finding: {e}")
    
    # Allow some time for the findings to appear
    L.info(f"Created {len(finding_ids)} sample findings. Waiting 60 seconds for findings to be processed...")
    time.sleep(60)
    
    return finding_ids

def create_trusted_ip_list(guardduty_client, detector_id):
    """
    Create a sample trusted IP list in GuardDuty.
    """
    try:
        # Get the current S3 bucket for the account to store the trusted IP list
        account_id = guardduty_client.get_detector(DetectorId=detector_id).get('ServiceRole').split(':')[4]
        region = guardduty_client._client_config.region_name
        
        # Create an S3 client to upload the trusted IP list
        s3_client = boto3.client('s3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
            region_name=region
        )
        
        # Create a unique bucket name for testing
        bucket_name = f"guardduty-trusted-ip-list-{account_id}-{int(time.time())}"
        
        try:
            # Create the bucket
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': region
                } if region != 'us-east-1' else {}
            )
            L.info(f"Created S3 bucket: {bucket_name}")
            
            # Generate a sample trusted IP list
            trusted_ips = [
                "192.0.2.0/24",  # TEST-NET-1
                "198.51.100.0/24",  # TEST-NET-2
                "203.0.113.0/24",  # TEST-NET-3
                "127.0.0.1/32",  # localhost
                "10.0.0.0/8",  # private network
                "172.16.0.0/12",  # private network
                "192.168.0.0/16"  # private network
            ]
            
            trusted_ip_content = "\n".join(trusted_ips)
            
            # Upload the trusted IP list to S3
            object_key = 'trusted-ip-list.txt'
            s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=trusted_ip_content
            )
            L.info(f"Uploaded trusted IP list to s3://{bucket_name}/{object_key}")
            
            # Create the trusted IP list in GuardDuty using the correct API
            list_name = f"Sample-TrustedIPList-{int(time.time())}"
            try:
                guardduty_client.create_ip_set(
                    DetectorId=detector_id,
                    Name=list_name,
                    Format='TXT',
                    Location=f"s3://{bucket_name}/{object_key}",
                    Activate=True
                )
                L.info(f"Created trusted IP list: {list_name}")
                return list_name
            except Exception as e:
                L.error(f"Error creating IP set: {e}")
                return None
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'BucketAlreadyOwnedByYou':
                L.warning(f"Bucket {bucket_name} already exists and is owned by you")
                return None
            else:
                L.error(f"Error creating S3 bucket: {e}")
                return None
                
    except Exception as e:
        L.error(f"Error creating trusted IP list: {e}")
        return None

def create_threat_intel_set(guardduty_client, detector_id):
    """
    Create a sample threat intelligence set in GuardDuty.
    """
    try:
        # Get the current S3 bucket for the account to store the threat intel set
        account_id = guardduty_client.get_detector(DetectorId=detector_id).get('ServiceRole').split(':')[4]
        region = guardduty_client._client_config.region_name
        
        # Create an S3 client to upload the threat intel set
        s3_client = boto3.client('s3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
            region_name=region
        )
        
        # Create a unique bucket name for testing
        bucket_name = f"guardduty-threat-intel-{account_id}-{int(time.time())}"
        
        try:
            # Create the bucket
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': region
                } if region != 'us-east-1' else {}
            )
            L.info(f"Created S3 bucket: {bucket_name}")
            
            # Generate a sample threat intel set (IP addresses for demonstration)
            threat_ips = [
                "100.0.0.1",
                "100.0.0.2",
                "100.0.0.3",
                "100.0.0.4",
                "100.0.0.5"
            ]
            
            threat_ip_content = "\n".join(threat_ips)
            
            # Upload the threat intel set to S3
            object_key = 'threat-intel-list.txt'
            s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=threat_ip_content
            )
            L.info(f"Uploaded threat intel set to s3://{bucket_name}/{object_key}")
            
            # Create the threat intel set in GuardDuty using the correct API
            set_name = f"Sample-ThreatIntelSet-{int(time.time())}"
            try:
                guardduty_client.create_threat_intel_set(
                    DetectorId=detector_id,
                    Name=set_name,
                    Format='TXT',
                    Location=f"s3://{bucket_name}/{object_key}",
                    Activate=True
                )
                L.info(f"Created threat intel set: {set_name}")
                return set_name
            except Exception as e:
                L.error(f"Error creating threat intel set: {e}")
                return None
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'BucketAlreadyOwnedByYou':
                L.warning(f"Bucket {bucket_name} already exists and is owned by you")
                return None
            else:
                L.error(f"Error creating S3 bucket: {e}")
                return None
                
    except Exception as e:
        L.error(f"Error creating threat intel set: {e}")
        return None

def get_recommendation_text(finding_type):
    """
    Get recommendation text based on finding type.
    """
    recommendations = {
        'Backdoor:EC2/C&CActivity.B': 'Examine the EC2 instance for signs of compromise. If this activity is unexpected, the instance might be compromised.',
        'CryptoCurrency:EC2/BitcoinTool.B': 'If you use this EC2 instance to mine or manage cryptocurrency, this finding could be expected. If not, your instance might be compromised.',
        'UnauthorizedAccess:EC2/SSHBruteForce': 'If this activity is unexpected, your instance might be compromised. Secure SSH by restricting security groups and using bastion hosts.',
        'Recon:EC2/PortProbeUnprotectedPort': 'Secure the reported unprotected port by using security groups, network ACLs, or a firewall.',
        'Trojan:EC2/BlackholeTraffic': 'Your EC2 instance is attempting to communicate with a blackhole IP address. Examine the instance for signs of compromise.',
        'Policy:S3/BucketBlockPublicAccessDisabled': 'Evaluate if your S3 bucket requires public access. If not, enable S3 Block Public Access for the bucket.',
        'PenTest:IAMUser/KaliLinux': 'If you are not using Kali Linux for security testing, this might indicate unauthorized penetration testing activity.',
        'Persistence:IAMUser/NetworkPermissions': 'Review the IAM user and verify if they should have network permissions. If not, revoke them and investigate.',
        'PrivilegeEscalation:IAMUser/AdministrativePermissions': 'Verify if this IAM user should have administrative permissions. If not, revoke them and investigate.',
        'Recon:IAMUser/ResourcePermissions': 'Monitor this IAM user for other suspicious activity. If this behavior is unexpected, the account might be compromised.',
        'Recon:IAMUser/UserPermissions': "If this activity is unexpected for this IAM user, consider restricting the user's permissions and investigate further.",
        'Discovery:S3/BucketEnumeration.Unusual': 'If this activity is unexpected, an IAM credential might be compromised. Rotate the credential and investigate.',
    }
    
    # Default recommendation
    default_recommendation = 'Review the finding details and determine if this activity is expected in your environment. If not, consider it a potential security threat and take appropriate action.'
    
    return recommendations.get(finding_type, default_recommendation)

def enable_sample_findings(guardduty_client, detector_id):
    """
    Enable the ability to create sample findings in GuardDuty.
    """
    try:
        L.info(f"Enabling sample findings generation for detector {detector_id}...")
        guardduty_client.update_detector(
            DetectorId=detector_id,
            FindingPublishingFrequency='FIFTEEN_MINUTES',
            Enable=True
        )
        L.info("Sample findings generation enabled successfully")
        return True
    except Exception as e:
        L.error(f"Error enabling sample findings generation: {e}")
        return False

def create_test_data():
    """
    Create test data in GuardDuty (detector, sample findings, trusted IP list, and threat intel set).
    """
    L.info("Starting GuardDuty test data generation...")
    
    try:
        # Connect to GuardDuty
        guardduty_client = connect_to_guardduty()
        L.info("Connected to GuardDuty successfully")
        
        # Verify or create detector
        detector_id = verify_or_create_detector(guardduty_client)
        
        if detector_id:
            # Enable sample findings
            enable_success = enable_sample_findings(guardduty_client, detector_id)
            
            if enable_success:
                # Create sample findings
                sample_findings = create_sample_findings(guardduty_client, detector_id, count=10)
                
                # Create a trusted IP list
                trusted_ip_list = create_trusted_ip_list(guardduty_client, detector_id)
                
                # Create a threat intel set
                threat_intel_set = create_threat_intel_set(guardduty_client, detector_id)
                
                L.info("Test data generation completed successfully!")
                
                summary = {
                    'detector_id': detector_id,
                    'sample_findings': len(sample_findings) if sample_findings else 0,
                    'trusted_ip_list': trusted_ip_list is not None,
                    'threat_intel_set': threat_intel_set is not None
                }
                
                L.info(f"Summary of created resources: {summary}")
                return True
            else:
                L.error("Failed to enable sample findings generation")
                return False
        else:
            L.error("Failed to verify or create GuardDuty detector")
            return False
            
    except Exception as e:
        L.error(f"Exception during test data generation: {e}")
        return False

def main():
    L.info("AWS GuardDuty Test Data Generator")
    
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
    
    success = create_test_data()
    
    if success:
        L.info("GuardDuty test data generation completed successfully!")
        return 0
    else:
        L.error("GuardDuty test data generation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())