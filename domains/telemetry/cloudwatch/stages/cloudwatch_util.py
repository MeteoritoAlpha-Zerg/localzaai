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
        logging.FileHandler('cloudwatch_verification.log')
    ]
)
L = logging.getLogger(__name__)

def verify_cloudwatch_credentials():
    """
    Verify AWS CloudWatch credentials by attempting to authenticate and access CloudWatch resources.
    
    Environment variables required:
    - AWS_REGION: AWS region (e.g., 'us-east-1')
    - AWS_ACCESS_KEY_ID: AWS Access Key ID
    - AWS_SECRET_ACCESS_KEY: AWS Secret Access Key
    - AWS_SESSION_TOKEN: Optional AWS Session Token for temporary credentials
    
    Returns:
    - True if credentials are valid and can access CloudWatch API
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
        L.info(f"Attempting to connect to AWS CloudWatch in region: {region}")
        
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=region
        )
        
        # Create CloudWatch Logs and CloudWatch Metrics clients
        logs_client = session.client('logs')
        cloudwatch_client = session.client('cloudwatch')
        
        # Test CloudWatch Logs API with a simple call
        L.info("Testing CloudWatch Logs API...")
        response = logs_client.describe_log_groups(limit=1)
        L.info(f"CloudWatch Logs API test successful. Response: {response}")
        
        # Test CloudWatch Metrics API with a simple call
        L.info("Testing CloudWatch Metrics API...")
        response = cloudwatch_client.list_metrics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[],
            RecentlyActive='PT3H'
        )
        L.info(f"CloudWatch Metrics API test successful. Response: {response}")
        
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
        error_msg = f"Exception occurred while connecting to CloudWatch: {e}"
        L.error(error_msg)
        return False

def get_cloudwatch_log_groups(limit=10):
    """
    Retrieve a list of CloudWatch log groups.
    
    Args:
        limit (int): Maximum number of log groups to retrieve
        
    Returns:
        list: List of log group information or None if failed
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
        
        # Create CloudWatch Logs client
        logs_client = session.client('logs')
        
        L.info(f"Retrieving list of log groups (limit: {limit})...")
        
        # Get log groups
        response = logs_client.describe_log_groups(limit=limit)
        log_groups = response.get('logGroups', [])
        
        log_groups_info = []
        for log_group in log_groups:
            info = {
                'name': log_group['logGroupName'],
                'arn': log_group.get('arn'),
                'creationTime': datetime.fromtimestamp(log_group['creationTime'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                'retentionInDays': log_group.get('retentionInDays', 'Never Expire'),
                'storedBytes': log_group.get('storedBytes', 0)
            }
            log_groups_info.append(info)
            L.info(f"Retrieved information for log group: {info['name']}")
        
        L.info(f"Successfully retrieved information for {len(log_groups_info)} log groups")
        return log_groups_info
        
    except Exception as e:
        L.error(f"Exception while retrieving log groups: {e}")
        return None

def get_cloudwatch_log_streams(log_group_name, limit=5):
    """
    Retrieve log streams from a specific log group.
    
    Args:
        log_group_name (str): Name of the log group to retrieve streams from
        limit (int): Maximum number of log streams to retrieve
        
    Returns:
        list: List of log streams or None if failed
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
        
        # Create CloudWatch Logs client
        logs_client = session.client('logs')
        
        L.info(f"Retrieving log streams from log group '{log_group_name}' (limit: {limit})...")
        
        # Get log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=limit
        )
        
        log_streams = response.get('logStreams', [])
        
        log_streams_info = []
        for stream in log_streams:
            info = {
                'name': stream['logStreamName'],
                'creationTime': datetime.fromtimestamp(stream['creationTime'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                'lastEventTimestamp': datetime.fromtimestamp(stream.get('lastEventTimestamp', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S') if 'lastEventTimestamp' in stream else 'N/A',
                'storedBytes': stream.get('storedBytes', 0)
            }
            log_streams_info.append(info)
            L.info(f"Retrieved information for log stream: {info['name']}")
        
        if log_streams_info:
            L.info(f"Successfully retrieved {len(log_streams_info)} log streams from '{log_group_name}'")
            return log_streams_info
        else:
            L.warning(f"No log streams found in '{log_group_name}'")
            return []
            
    except Exception as e:
        L.error(f"Exception while retrieving log streams from '{log_group_name}': {e}")
        return None

def get_cloudwatch_metrics(namespace=None, limit=10):
    """
    Retrieve CloudWatch metrics from a specific namespace or all namespaces.
    
    Args:
        namespace (str): Optional metric namespace to filter by
        limit (int): Maximum number of metrics to retrieve
        
    Returns:
        dict: Dict of namespaces and their metrics or None if failed
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
        
        # Create CloudWatch client
        cloudwatch_client = session.client('cloudwatch')
        
        # If namespace is not specified, get common AWS namespaces
        if not namespace:
            namespaces = ['AWS/EC2', 'AWS/Lambda', 'AWS/S3', 'AWS/RDS', 'AWS/DynamoDB']
        else:
            namespaces = [namespace]
        
        L.info(f"Retrieving metrics from namespaces: {namespaces} (limit per namespace: {limit})...")
        
        results = {}
        
        for ns in namespaces:
            # List metrics in the namespace
            response = cloudwatch_client.list_metrics(
                Namespace=ns,
                Dimensions=[]
            )
            
            metrics = response.get('Metrics', [])
            
            if metrics:
                results[ns] = []
                for metric in metrics:
                    metric_info = {
                        'name': metric['MetricName'],
                        'namespace': metric['Namespace'],
                        'dimensions': metric.get('Dimensions', [])
                    }
                    results[ns].append(metric_info)
                    L.info(f"Retrieved information for metric: {metric_info['name']} in namespace {ns}")
                
                L.info(f"Successfully retrieved {len(results[ns])} metrics from namespace '{ns}'")
            else:
                L.warning(f"No metrics found in namespace '{ns}'")
        
        if results:
            return results
        else:
            L.warning("No metrics found in any namespace")
            return {}
            
    except Exception as e:
        L.error(f"Exception while retrieving metrics: {e}")
        return None

def get_metric_data(namespace, metric_name, dimensions=None, period=300, start_time_offset=3600, end_time_offset=0):
    """
    Retrieve CloudWatch metric data for the specified metric.
    
    Args:
        namespace (str): Metric namespace
        metric_name (str): Name of the metric to retrieve data for
        dimensions (list): List of dimension dicts with Name and Value keys
        period (int): The granularity, in seconds, of the returned data points
        start_time_offset (int): Seconds ago to start retrieving data from
        end_time_offset (int): Seconds ago to end retrieving data at
        
    Returns:
        dict: Metric data or None if failed
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
        
        # Create CloudWatch client
        cloudwatch_client = session.client('cloudwatch')
        
        if dimensions is None:
            dimensions = []
        
        # Calculate start and end times
        end_time = datetime.utcnow() - timedelta(seconds=end_time_offset)
        start_time = end_time - timedelta(seconds=start_time_offset)
        
        L.info(f"Retrieving data for metric '{metric_name}' in namespace '{namespace}'...")
        L.info(f"Time range: {start_time} to {end_time}, period: {period} seconds")
        
        # Get metric data
        response = cloudwatch_client.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'metric1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': namespace,
                            'MetricName': metric_name,
                            'Dimensions': dimensions
                        },
                        'Period': period,
                        'Stat': 'Average'
                    },
                    'ReturnData': True
                },
            ],
            StartTime=start_time,
            EndTime=end_time
        )
        
        results = response.get('MetricDataResults', [])
        
        if results and results[0]['Values']:
            data_points = []
            timestamps = results[0]['Timestamps']
            values = results[0]['Values']
            
            for i in range(len(timestamps)):
                data_points.append({
                    'timestamp': timestamps[i].strftime('%Y-%m-%d %H:%M:%S'),
                    'value': values[i]
                })
            
            L.info(f"Successfully retrieved {len(data_points)} data points for metric '{metric_name}'")
            
            return {
                'namespace': namespace,
                'metric_name': metric_name,
                'dimensions': dimensions,
                'data_points': data_points
            }
        else:
            L.warning(f"No data found for metric '{metric_name}' in namespace '{namespace}'")
            return {
                'namespace': namespace,
                'metric_name': metric_name,
                'dimensions': dimensions,
                'data_points': []
            }
            
    except Exception as e:
        L.error(f"Exception while retrieving metric data: {e}")
        return None

def test_cloudwatch_logs_and_metrics():
    """
    Test retrieving log groups, log streams, and metrics from CloudWatch.
    
    Returns:
        bool: True if tests passed, False otherwise
    """
    L.info("\n=== Testing Log Group Retrieval ===")
    log_groups_data = get_cloudwatch_log_groups(limit=5)
    
    if not log_groups_data:
        L.warning("No log groups found or failed to retrieve log groups")
        log_groups_available = False
    else:
        L.info(f"✅ Successfully retrieved {len(log_groups_data)} log groups")
        
        # Display log group names
        log_group_names = [group.get('name') for group in log_groups_data]
        L.info(f"Log Groups: {', '.join(log_group_names)}")
        log_groups_available = True
    
    # Test retrieving log streams if log groups are available
    if log_groups_available and log_groups_data:
        L.info("\n=== Testing Log Stream Retrieval ===")
        test_log_group = log_groups_data[0]['name']
        
        L.info(f"Attempting to retrieve log streams from '{test_log_group}'...")
        log_streams_data = get_cloudwatch_log_streams(test_log_group, limit=3)
        
        if log_streams_data and len(log_streams_data) > 0:
            L.info(f"✅ Successfully retrieved {len(log_streams_data)} log streams from '{test_log_group}'")
            
            # Display log stream names
            log_stream_names = [stream.get('name') for stream in log_streams_data]
            L.info(f"Log Streams: {', '.join(log_stream_names)}")
        else:
            L.warning(f"No log streams found in '{test_log_group}' or failed to retrieve log streams")
    
    # Test retrieving metrics
    L.info("\n=== Testing Metric Retrieval ===")
    metrics_data = get_cloudwatch_metrics(namespace='AWS/EC2', limit=5)
    
    if not metrics_data:
        L.warning("No metrics found or failed to retrieve metrics")
        metrics_available = False
    else:
        L.info(f"✅ Successfully retrieved metrics from {len(metrics_data)} namespaces")
        
        # Display metric namespaces and counts
        for namespace, metrics in metrics_data.items():
            L.info(f"Namespace '{namespace}': {len(metrics)} metrics")
            
            # Display a few metric names
            if metrics:
                metric_names = [metric.get('name') for metric in metrics[:3]]
                L.info(f"Sample metrics: {', '.join(metric_names)}")
        
        metrics_available = True
    
    # Test retrieving metric data if metrics are available
    if metrics_available and metrics_data:
        L.info("\n=== Testing Metric Data Retrieval ===")
        
        # Find a namespace and metric to test
        test_namespace = next(iter(metrics_data.keys()))
        test_metric = metrics_data[test_namespace][0]['name'] if metrics_data[test_namespace] else None
        
        if test_metric:
            L.info(f"Attempting to retrieve data for metric '{test_metric}' in namespace '{test_namespace}'...")
            metric_data = get_metric_data(test_namespace, test_metric)
            
            if metric_data and metric_data.get('data_points'):
                L.info(f"✅ Successfully retrieved {len(metric_data['data_points'])} data points for metric '{test_metric}'")
                
                # Display a sample data point
                if metric_data['data_points']:
                    sample_point = metric_data['data_points'][0]
                    L.info(f"Sample data point: {sample_point}")
            else:
                L.warning(f"No data found for metric '{test_metric}' in namespace '{test_namespace}' or failed to retrieve metric data")
    
    # Return success if at least log groups or metrics are available
    return log_groups_available or metrics_available

def main():
    L.info("Starting AWS CloudWatch credential verification")
    
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
    success = verify_cloudwatch_credentials()
    
    if not success:
        L.error("Basic credential verification failed")
        return 1
    
    # Extended testing - Logs and Metrics
    L.info("\n=== Extended Verification: Logs and Metrics ===")
    test_success = test_cloudwatch_logs_and_metrics()
    
    if success and test_success:
        L.info("All credential verification tests completed successfully")
        return 0
    elif success:
        L.warning("Basic verification passed but log/metric tests found limited or no data")
        return 0  # Still return success since basic auth worked
    else:
        L.error("Credential verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())