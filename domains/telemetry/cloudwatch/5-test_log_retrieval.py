# 5-test_log_retrieval.py

async def test_log_retrieval(zerg_state=None):
    """Test CloudWatch log events retrieval for a selected log group"""
    print("Attempting to authenticate using CloudWatch connector")

    assert zerg_state, "this test requires valid zerg_state"

    aws_region = zerg_state.get("aws_region").get("value")
    aws_access_key_id = zerg_state.get("aws_access_key_id").get("value")
    aws_secret_access_key = zerg_state.get("aws_secret_access_key").get("value")
    aws_session_token = zerg_state.get("aws_session_token", {}).get("value")
    cloudwatch_log_retention_days = int(zerg_state.get("cloudwatch_log_retention_days", {}).get("value", 7))

    from connectors.cloudwatch.config import CloudWatchConnectorConfig
    from connectors.cloudwatch.connector import CloudWatchConnector
    from connectors.cloudwatch.tools import CloudWatchConnectorTools, GetCloudWatchLogsInput
    from connectors.cloudwatch.target import CloudWatchTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    from datetime import datetime, timedelta

    # set up the config
    config = CloudWatchConnectorConfig(
        region=aws_region,
        access_key_id=aws_access_key_id,
        secret_access_key=aws_secret_access_key,
        session_token=aws_session_token
    )
    assert isinstance(config, ConnectorConfig), "CloudWatchConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CloudWatchConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CloudWatchConnector should be of type Connector"

    # get query target options to find available log groups
    cloudwatch_query_target_options = await connector.get_query_target_options()
    assert isinstance(cloudwatch_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select log groups to target
    log_group_selector = None
    for selector in cloudwatch_query_target_options.selectors:
        if selector.type == 'log_groups':  
            log_group_selector = selector
            break

    assert log_group_selector, "failed to retrieve log group selector from query target options"
    assert isinstance(log_group_selector.values, list), "log_group_selector values must be a list"
    
    # Select the first log group for testing
    log_group = log_group_selector.values[0] if log_group_selector.values else None
    print(f"Selected log group for testing: {log_group}")
    assert log_group, "failed to retrieve log group from log group selector"

    # set up the target with selected log group
    target = CloudWatchTarget(log_groups=[log_group])
    assert isinstance(target, ConnectorTargetInterface), "CloudWatchTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # find the get_cloudwatch_logs tool and execute it
    get_logs_tool = next((tool for tool in tools if tool.name == "get_cloudwatch_logs"), None)
    assert get_logs_tool, "get_cloudwatch_logs tool not found in available tools"
    
    # Calculate time range for logs (default: last 7 days)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=cloudwatch_log_retention_days)
    
    # Execute the tool to retrieve logs for the selected log group
    logs_result = await get_logs_tool.execute(
        log_group_name=log_group,
        start_time=start_time.timestamp() * 1000,  # Convert to milliseconds
        end_time=end_time.timestamp() * 1000,      # Convert to milliseconds
        limit=100  # Request a reasonable number of log events
    )
    logs = logs_result.raw_result

    print("Type of returned logs:", type(logs))
    
    # Verify that logs is a list of log events
    assert isinstance(logs, list), "logs should be a list of log events"
    print(f"Retrieved {len(logs)} log events from {log_group}")
    
    # If there are logs, verify their structure
    if logs:
        # Limit the number of logs to check if there are many
        logs_to_check = logs[:5] if len(logs) > 5 else logs
        
        for log_event in logs_to_check:
            # Verify essential log event fields
            assert "timestamp" in log_event, "Each log event should have a 'timestamp' field"
            assert "message" in log_event, "Each log event should have a 'message' field"
            assert "logStreamName" in log_event, "Each log event should have a 'logStreamName' field"
            
            # Verify timestamp is within requested range
            assert start_time.timestamp() * 1000 <= log_event["timestamp"] <= end_time.timestamp() * 1000, \
                f"Log event timestamp {log_event['timestamp']} is outside requested range"
            
            # Verify event belongs to requested log group
            if "logGroupName" in log_event:
                assert log_event["logGroupName"] == log_group, \
                    f"Log event group {log_event['logGroupName']} does not match requested log group {log_group}"
        
        # Log the structure of the first event for debugging
        print(f"Example log event structure: {logs[0]}")
    else:
        print(f"No log events found in {log_group} for the specified time range")
    
    # Verify the tool works even if no logs are found (should return empty list, not error)
    assert logs is not None, "Log retrieval tool should return a list (even if empty) not None"

    print(f"Successfully tested log retrieval for CloudWatch log group: {log_group}")

    return True