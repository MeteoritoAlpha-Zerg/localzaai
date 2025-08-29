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

def connect_to_cloudwatch():
    """
    Connect to AWS CloudWatch using environment variables.
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
    
    # Create CloudWatch Logs and CloudWatch Metrics clients
    logs_client = session.client('logs')
    cloudwatch_client = session.client('cloudwatch')
    
    return logs_client, cloudwatch_client

def create_log_groups(logs_client, count=3):
    """
    Create test log groups in CloudWatch Logs.
    """
    L.info(f"Creating {count} test log groups...")
    
    log_group_names = []
    
    # Define test log group prefixes
    prefixes = ['app', 'api', 'lambda', 'system', 'web']
    environments = ['dev', 'test', 'staging', 'prod']
    
    for i in range(count):
        prefix = random.choice(prefixes)
        env = random.choice(environments)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        log_group_name = f"/test/{prefix}-{env}-{timestamp}-{i+1}"
        
        try:
            logs_client.create_log_group(logGroupName=log_group_name)
            log_group_names.append(log_group_name)
            L.info(f"Created log group: {log_group_name}")
            
            # Set retention policy (7 days)
            logs_client.put_retention_policy(
                logGroupName=log_group_name,
                retentionInDays=7
            )
            L.info(f"Set retention policy to 7 days for log group: {log_group_name}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'ResourceAlreadyExistsException':
                L.warning(f"Log group already exists: {log_group_name}")
                log_group_names.append(log_group_name)
            else:
                L.error(f"Failed to create log group: {e}")
        except Exception as e:
            L.error(f"Exception creating log group: {e}")
    
    return log_group_names

def create_log_streams(logs_client, log_group_names, streams_per_group=2):
    """
    Create test log streams in the specified log groups.
    """
    L.info(f"Creating {streams_per_group} log streams per log group...")
    
    log_streams = {}
    
    # Define test log stream types
    stream_types = ['application', 'access', 'error', 'system', 'debug']
    
    for log_group_name in log_group_names:
        log_streams[log_group_name] = []
        
        for i in range(streams_per_group):
            stream_type = random.choice(stream_types)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            log_stream_name = f"{stream_type}-{timestamp}-{i+1}"
            
            try:
                logs_client.create_log_stream(
                    logGroupName=log_group_name,
                    logStreamName=log_stream_name
                )
                log_streams[log_group_name].append(log_stream_name)
                L.info(f"Created log stream: {log_stream_name} in log group: {log_group_name}")
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                if error_code == 'ResourceAlreadyExistsException':
                    L.warning(f"Log stream already exists: {log_stream_name} in log group: {log_group_name}")
                    log_streams[log_group_name].append(log_stream_name)
                else:
                    L.error(f"Failed to create log stream: {e}")
            except Exception as e:
                L.error(f"Exception creating log stream: {e}")
    
    return log_streams

def generate_log_events(logs_client, log_streams, events_per_stream=20):
    """
    Generate and put test log events into the specified log streams.
    """
    L.info(f"Generating {events_per_stream} log events per stream...")
    
    # Define log event templates
    info_templates = [
        "Application started with version {version}",
        "User {user_id} logged in from {ip_address}",
        "Request processed successfully in {duration} ms",
        "Cache hit ratio: {ratio}%",
        "API request to {endpoint} completed with status {status}"
    ]
    
    warning_templates = [
        "High memory usage detected: {memory}%",
        "Slow database query detected: {query_time} ms",
        "Rate limiting applied to IP {ip_address}",
        "Connection pool running low: {connections} available",
        "Deprecated API endpoint {endpoint} called"
    ]
    
    error_templates = [
        "Error connecting to database: {error_message}",
        "Exception in thread {thread_name}: {exception}",
        "Failed to process request: {reason}",
        "Authentication failed for user {user_id}: {reason}",
        "API request to {endpoint} failed with status {status}"
    ]
    
    debug_templates = [
        "Function {function_name} called with params: {params}",
        "Database query executed: {query}",
        "Cache entry added for key: {key}",
        "Thread {thread_id} state changed to {state}",
        "Config loaded from {source} with {settings} settings"
    ]
    
    events_generated = 0
    sequence_tokens = {}
    
    # Define function to generate random log message
    def generate_log_message(log_level):
        if log_level == "INFO":
            template = random.choice(info_templates)
        elif log_level == "WARNING":
            template = random.choice(warning_templates)
        elif log_level == "ERROR":
            template = random.choice(error_templates)
        else:  # DEBUG
            template = random.choice(debug_templates)
        
        # Fill in template variables with random values
        if "{version}" in template:
            template = template.replace("{version}", f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}")
        if "{user_id}" in template:
            template = template.replace("{user_id}", f"user-{random.randint(1000, 9999)}")
        if "{ip_address}" in template:
            template = template.replace("{ip_address}", f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}")
        if "{duration}" in template:
            template = template.replace("{duration}", str(random.randint(5, 500)))
        if "{ratio}" in template:
            template = template.replace("{ratio}", str(random.randint(50, 99)))
        if "{endpoint}" in template:
            template = template.replace("{endpoint}", f"/api/v1/{random.choice(['users', 'orders', 'products', 'customers', 'auth'])}")
        if "{status}" in template:
            status_codes = [200, 201, 204, 400, 401, 403, 404, 500]
            template = template.replace("{status}", str(random.choice(status_codes)))
        if "{memory}" in template:
            template = template.replace("{memory}", str(random.randint(70, 95)))
        if "{query_time}" in template:
            template = template.replace("{query_time}", str(random.randint(100, 5000)))
        if "{connections}" in template:
            template = template.replace("{connections}", str(random.randint(1, 10)))
        if "{error_message}" in template:
            error_messages = [
                "Connection refused", 
                "Timeout expired", 
                "Authentication failed",
                "Invalid query syntax",
                "Too many connections"
            ]
            template = template.replace("{error_message}", random.choice(error_messages))
        if "{thread_name}" in template:
            template = template.replace("{thread_name}", f"Thread-{random.randint(1, 20)}")
        if "{exception}" in template:
            exceptions = [
                "NullPointerException", 
                "IndexOutOfBoundsException", 
                "IllegalArgumentException",
                "RuntimeException",
                "IOException"
            ]
            template = template.replace("{exception}", random.choice(exceptions))
        if "{reason}" in template:
            reasons = [
                "Invalid input", 
                "Resource not found", 
                "Permission denied",
                "Rate limit exceeded",
                "Internal server error"
            ]
            template = template.replace("{reason}", random.choice(reasons))
        if "{function_name}" in template:
            functions = [
                "processRequest", 
                "validateInput", 
                "authenticateUser",
                "queryDatabase",
                "cacheResult"
            ]
            template = template.replace("{function_name}", random.choice(functions))
        if "{params}" in template:
            template = template.replace("{params}", json.dumps({"id": random.randint(1000, 9999), "limit": random.randint(10, 100)}))
        if "{query}" in template:
            queries = [
                "SELECT * FROM users WHERE id = 123", 
                "UPDATE products SET stock = 10 WHERE id = 456", 
                "INSERT INTO orders VALUES (789, 'pending')",
                "DELETE FROM sessions WHERE expiry < NOW()",
                "SELECT COUNT(*) FROM events GROUP BY type"
            ]
            template = template.replace("{query}", random.choice(queries))
        if "{key}" in template:
            template = template.replace("{key}", f"cache-key-{random.randint(1000, 9999)}")
        if "{thread_id}" in template:
            template = template.replace("{thread_id}", str(random.randint(1, 50)))
        if "{state}" in template:
            states = ["RUNNING", "WAITING", "SLEEPING", "BLOCKED", "TERMINATED"]
            template = template.replace("{state}", random.choice(states))
        if "{source}" in template:
            sources = ["file", "database", "environment", "remote", "default"]
            template = template.replace("{source}", random.choice(sources))
        if "{settings}" in template:
            template = template.replace("{settings}", str(random.randint(5, 50)))
        
        return template

    # Process each log group and stream
    for log_group_name, stream_names in log_streams.items():
        for log_stream_name in stream_names:
            log_events = []
            
            # Initialize sequence token
            sequence_token = None
            
            for i in range(events_per_stream):
                # Generate random timestamp within the last 24 hours
                timestamp = int((datetime.now() - timedelta(hours=random.randint(0, 24), 
                                                            minutes=random.randint(0, 59), 
                                                            seconds=random.randint(0, 59))).timestamp() * 1000)
                
                # Determine log level
                log_level_choices = ["INFO", "WARNING", "ERROR", "DEBUG"]
                weights = [0.7, 0.15, 0.1, 0.05]  # 70% INFO, 15% WARNING, 10% ERROR, 5% DEBUG
                log_level = random.choices(log_level_choices, weights=weights, k=1)[0]
                
                # Generate the log message
                message = f"[{log_level}] {generate_log_message(log_level)}"
                
                # Add to batch
                log_events.append({
                    'timestamp': timestamp,
                    'message': message
                })
                
                # CloudWatch Logs requires events to be sorted by timestamp
                log_events.sort(key=lambda x: x['timestamp'])
            
            try:
                # Get the sequence token if needed (for subsequent PutLogEvents calls)
                if log_group_name in sequence_tokens and log_stream_name in sequence_tokens[log_group_name]:
                    sequence_token = sequence_tokens[log_group_name][log_stream_name]
                
                # Put log events in batches (CloudWatch has a limit of 10,000 log events in a single request)
                batch_size = 100
                for i in range(0, len(log_events), batch_size):
                    batch = log_events[i:i+batch_size]
                    
                    # Add sequence token if we have one
                    kwargs = {
                        'logGroupName': log_group_name,
                        'logStreamName': log_stream_name,
                        'logEvents': batch
                    }
                    
                    if sequence_token:
                        kwargs['sequenceToken'] = sequence_token
                    
                    # Put log events
                    response = logs_client.put_log_events(**kwargs)
                    
                    # Update sequence token for next batch
                    if 'nextSequenceToken' in response:
                        if log_group_name not in sequence_tokens:
                            sequence_tokens[log_group_name] = {}
                        sequence_tokens[log_group_name][log_stream_name] = response['nextSequenceToken']
                        sequence_token = response['nextSequenceToken']
                    
                    events_generated += len(batch)
                    L.info(f"Sent {len(batch)} log events to stream {log_stream_name} in group {log_group_name}")
                    
                    # Small delay to avoid throttling
                    time.sleep(0.1)
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                error_message = e.response.get('Error', {}).get('Message', '')
                
                # Handle invalid sequence token
                if error_code == 'InvalidSequenceTokenException' and 'The given sequenceToken is invalid' in error_message:
                    # Extract the expected sequence token from the error message
                    import re
                    match = re.search(r'sequenceToken is: (.+)$', error_message)
                    if match:
                        correct_token = match.group(1)
                        L.warning(f"Invalid sequence token. Retrying with correct token: {correct_token}")
                        
                        # Update our sequence token and retry
                        if log_group_name not in sequence_tokens:
                            sequence_tokens[log_group_name] = {}
                        sequence_tokens[log_group_name][log_stream_name] = correct_token
                        
                        # Don't count as generated, will retry in next iteration
                    else:
                        L.error(f"Could not extract correct sequence token from error message: {error_message}")
                else:
                    L.error(f"Error putting log events to {log_stream_name} in {log_group_name}: {e}")
            except Exception as e:
                L.error(f"Exception putting log events: {e}")
    
    L.info(f"Generated and sent a total of {events_generated} log events")
    return events_generated

def put_custom_metrics(cloudwatch_client, namespaces=None, metrics_per_namespace=3, data_points_per_metric=24):
    """
    Generate and put custom metrics data into CloudWatch Metrics.
    
    Args:
        cloudwatch_client: Boto3 CloudWatch client
        namespaces: List of custom namespaces to use (if None, will generate)
        metrics_per_namespace: Number of metrics to create per namespace
        data_points_per_metric: Number of data points to generate per metric
        
    Returns:
        dict: Information about the metrics created
    """
    L.info(f"Generating custom metrics data...")
    
    # Define default namespaces if none provided
    if not namespaces:
        namespaces = [
            'Custom/Application', 
            'Custom/Database', 
            'Custom/API',
            'Custom/System'
        ]
    
    # Define metric templates
    metric_templates = {
        'Custom/Application': [
            {'name': 'RequestLatency', 'unit': 'Milliseconds'},
            {'name': 'RequestCount', 'unit': 'Count'},
            {'name': 'ErrorCount', 'unit': 'Count'},
            {'name': 'UserLogins', 'unit': 'Count'},
            {'name': 'CacheHitRatio', 'unit': 'Percent'}
        ],
        'Custom/Database': [
            {'name': 'QueryLatency', 'unit': 'Milliseconds'},
            {'name': 'ConnectionCount', 'unit': 'Count'},
            {'name': 'DatabaseCPUUtilization', 'unit': 'Percent'},
            {'name': 'DatabaseMemoryUtilization', 'unit': 'Percent'},
            {'name': 'TransactionCount', 'unit': 'Count'}
        ],
        'Custom/API': [
            {'name': 'APILatency', 'unit': 'Milliseconds'},
            {'name': 'APIRequestCount', 'unit': 'Count'},
            {'name': 'APIErrorRate', 'unit': 'Percent'},
            {'name': 'ThrottledRequests', 'unit': 'Count'},
            {'name': 'CacheHitRate', 'unit': 'Percent'}
        ],
        'Custom/System': [
            {'name': 'CPUUtilization', 'unit': 'Percent'},
            {'name': 'MemoryUtilization', 'unit': 'Percent'},
            {'name': 'DiskSpaceUtilization', 'unit': 'Percent'},
            {'name': 'NetworkIn', 'unit': 'Bytes'},
            {'name': 'NetworkOut', 'unit': 'Bytes'}
        ]
    }
    
    # Add generic metrics for any namespaces not in our templates
    generic_metrics = [
        {'name': 'Count', 'unit': 'Count'},
        {'name': 'Latency', 'unit': 'Milliseconds'},
        {'name': 'ErrorRate', 'unit': 'Percent'},
        {'name': 'Utilization', 'unit': 'Percent'},
        {'name': 'Throughput', 'unit': 'Count/Second'}
    ]
    
    # Make sure all namespaces have metric templates
    for ns in namespaces:
        if ns not in metric_templates:
            metric_templates[ns] = generic_metrics
    
    # Define dimensions for metrics
    dimension_templates = {
        'Custom/Application': [
            {'Name': 'Environment', 'Values': ['Production', 'Staging', 'Development']},
            {'Name': 'Service', 'Values': ['Frontend', 'Backend', 'Auth', 'Payment']},
            {'Name': 'Region', 'Values': ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-northeast-1']}
        ],
        'Custom/Database': [
            {'Name': 'DatabaseName', 'Values': ['Users', 'Products', 'Orders', 'Analytics']},
            {'Name': 'InstanceType', 'Values': ['Primary', 'Replica', 'Backup']},
            {'Name': 'Engine', 'Values': ['MySQL', 'PostgreSQL', 'MongoDB', 'DynamoDB']}
        ],
        'Custom/API': [
            {'Name': 'Endpoint', 'Values': ['/users', '/products', '/orders', '/auth']},
            {'Name': 'Method', 'Values': ['GET', 'POST', 'PUT', 'DELETE']},
            {'Name': 'Version', 'Values': ['v1', 'v2', 'v3']}
        ],
        'Custom/System': [
            {'Name': 'InstanceId', 'Values': ['i-12345', 'i-67890', 'i-abcdef']},
            {'Name': 'InstanceType', 'Values': ['t2.micro', 't2.small', 'm5.large']},
            {'Name': 'AvailabilityZone', 'Values': ['us-east-1a', 'us-east-1b', 'us-east-1c']}
        ]
    }
    
    # Generic dimensions for any namespaces not in our templates
    generic_dimensions = [
        {'Name': 'Service', 'Values': ['ServiceA', 'ServiceB', 'ServiceC']},
        {'Name': 'Environment', 'Values': ['Prod', 'Stage', 'Dev']},
        {'Name': 'Instance', 'Values': ['Instance1', 'Instance2', 'Instance3']}
    ]
    
    # Make sure all namespaces have dimension templates
    for ns in namespaces:
        if ns not in dimension_templates:
            dimension_templates[ns] = generic_dimensions
    
    # Track metrics created
    metrics_created = {}
    
    for namespace in namespaces:
        metrics_created[namespace] = []
        
        # Select metrics for this namespace
        available_metrics = metric_templates.get(namespace, generic_metrics)
        if len(available_metrics) > metrics_per_namespace:
            selected_metrics = random.sample(available_metrics, metrics_per_namespace)
        else:
            selected_metrics = available_metrics
        
        # Get dimensions for this namespace
        available_dimensions = dimension_templates.get(namespace, generic_dimensions)
        
        for metric in selected_metrics:
            metric_name = metric['name']
            unit = metric['unit']
            
            # For this metric, randomly select 1 or 2 dimensions
            num_dimensions = random.randint(1, min(2, len(available_dimensions)))
            selected_dimensions = random.sample(available_dimensions, num_dimensions)
            
            # Create dimension combinations
            dimension_combos = []
            for dim in selected_dimensions:
                # Select a random value for each dimension
                dim_value = random.choice(dim['Values'])
                dimension_combos.append({'Name': dim['Name'], 'Value': dim_value})
            
            # Generate data points over the last 24 hours
            end_time = datetime.utcnow()
            
            # Calculate the time interval for data points (in seconds)
            interval = (24 * 60 * 60) // data_points_per_metric
            
            L.info(f"Putting metric data for {metric_name} in namespace {namespace}...")
            
            # Generate and put data points in batches
            batch_size = 20  # CloudWatch allows up to 20 data points per PutMetricData call
            metrics_data = []
            
            for i in range(data_points_per_metric):
                # Calculate timestamp for this data point
                timestamp = end_time - timedelta(seconds=i * interval)
                
                # Generate random value based on unit
                if unit == 'Count' or unit == 'Count/Second':
                    value = random.randint(1, 100)
                elif unit == 'Milliseconds':
                    value = random.randint(5, 500)
                elif unit == 'Percent':
                    value = random.uniform(1.0, 100.0)
                elif unit == 'Bytes':
                    value = random.randint(1024, 10485760)  # 1KB to 10MB
                else:
                    value = random.uniform(1.0, 100.0)
                
                # Add to batch
                metrics_data.append({
                    'MetricName': metric_name,
                    'Dimensions': dimension_combos,
                    'Timestamp': timestamp,
                    'Value': value,
                    'Unit': unit
                })
                
                # If batch is full or this is the last data point, put the data
                if len(metrics_data) >= batch_size or i == data_points_per_metric - 1:
                    try:
                        cloudwatch_client.put_metric_data(
                            Namespace=namespace,
                            MetricData=metrics_data
                        )
                        L.info(f"Put {len(metrics_data)} data points for {metric_name}")
                    except Exception as e:
                        L.error(f"Error putting metric data for {metric_name}: {e}")
                    
                    # Clear batch for next iteration
                    metrics_data = []
                    
                    # Small delay to avoid throttling
                    time.sleep(0.1)
            
            # Record the metric we created
            metrics_created[namespace].append({
                'name': metric_name,
                'unit': unit,
                'dimensions': dimension_combos
            })
    
    L.info(f"Successfully created metrics in {len(metrics_created)} namespaces")
    return metrics_created

def create_test_data():
    """
    Create test data in CloudWatch (log groups, log streams, log events, and custom metrics).
    """
    L.info("Starting CloudWatch test data generation...")
    
    try:
        # Connect to CloudWatch
        logs_client, cloudwatch_client = connect_to_cloudwatch()
        L.info("Connected to CloudWatch successfully")
        
        # Create log groups
        log_group_names = create_log_groups(logs_client, count=3)
        
        if log_group_names:
            # Create log streams in the log groups
            log_streams = create_log_streams(logs_client, log_group_names, streams_per_group=2)
            
            # Generate log events in the log streams
            events_count = generate_log_events(logs_client, log_streams, events_per_stream=20)
            
            # Generate custom metrics
            metrics_data = put_custom_metrics(
                cloudwatch_client, 
                namespaces=None,  # Use default namespaces
                metrics_per_namespace=3,
                data_points_per_metric=24  # One for each hour in the last day
            )
            
            L.info("Test data generation completed successfully!")
            
            summary = {
                'log_groups': len(log_group_names),
                'log_streams': sum(len(streams) for streams in log_streams.values()) if log_streams else 0,
                'log_events': events_count,
                'metric_namespaces': len(metrics_data) if metrics_data else 0,
                'metrics': sum(len(metrics) for metrics in metrics_data.values()) if metrics_data else 0
            }
            
            L.info(f"Summary of created resources: {summary}")
            return True
            
        else:
            L.error("Failed to create any log groups")
            return False
            
    except Exception as e:
        L.error(f"Exception during test data generation: {e}")
        return False

def main():
    L.info("AWS CloudWatch Test Data Generator")
    
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
        L.info("CloudWatch test data generation completed successfully!")
        return 0
    else:
        L.error("CloudWatch test data generation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())