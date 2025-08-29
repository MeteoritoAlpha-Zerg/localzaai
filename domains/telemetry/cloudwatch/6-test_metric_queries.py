# 6-test_metric_queries.py

async def test_metric_queries(zerg_state=None):
    """Test CloudWatch metric queries with filters, dimensions, and time ranges"""
    print("Attempting to authenticate using CloudWatch connector")

    assert zerg_state, "this test requires valid zerg_state"

    aws_region = zerg_state.get("aws_region").get("value")
    aws_access_key_id = zerg_state.get("aws_access_key_id").get("value")
    aws_secret_access_key = zerg_state.get("aws_secret_access_key").get("value")
    aws_session_token = zerg_state.get("aws_session_token", {}).get("value")
    cloudwatch_api_request_timeout = int(zerg_state.get("cloudwatch_api_request_timeout", {}).get("value", 30))

    from connectors.cloudwatch.config import CloudWatchConnectorConfig
    from connectors.cloudwatch.connector import CloudWatchConnector
    from connectors.cloudwatch.tools import CloudWatchConnectorTools, QueryCloudWatchMetricsInput
    from connectors.cloudwatch.target import CloudWatchTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    from datetime import datetime, timedelta
    import time

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

    # Get the get_cloudwatch_metrics tool first to find available metrics
    get_metrics_tool = next((tool for tool in tools if tool.name == "get_cloudwatch_metrics"), None)
    assert get_metrics_tool, "get_cloudwatch_metrics tool not found in available tools"
    
    metrics_result = await get_metrics_tool.execute()
    metrics = metrics_result.raw_result
    
    assert isinstance(metrics, dict), "metrics should be a dictionary of namespaces"
    assert len(metrics) > 0, "metrics should not be empty"
    
    # Select a namespace and metric for querying
    namespace = next(iter(metrics.keys()))
    namespace_metrics = metrics[namespace]
    assert len(namespace_metrics) > 0, f"No metrics found in namespace {namespace}"
    
    metric = namespace_metrics[0]
    metric_name = metric["MetricName"]
    print(f"Selected metric for testing: {namespace}:{metric_name}")
    
    # Find dimensions if available
    dimensions = metric.get("Dimensions", [])
    dimension_dict = {}
    for dimension in dimensions:
        dimension_dict[dimension["Name"]] = dimension["Value"]
    
    # find the query_cloudwatch_metrics tool
    query_metrics_tool = next((tool for tool in tools if tool.name == "query_cloudwatch_metrics"), None)
    assert query_metrics_tool, "query_cloudwatch_metrics tool not found in available tools"
    
    # Set up the time range (last 3 hours)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=3)
    
    # Define the statistics to retrieve
    statistics = ["Average", "Maximum", "Minimum", "Sum", "SampleCount"]
    
    print(f"Querying metric {metric_name} in namespace {namespace} with dimensions {dimension_dict}")
    
    # Execute the tool to query the selected metric
    query_result = await query_metrics_tool.execute(
        namespace=namespace,
        metric_name=metric_name,
        dimensions=dimension_dict,
        start_time=start_time.timestamp(),
        end_time=end_time.timestamp(),
        period=60,  # 1-minute periods
        statistics=statistics
    )
    
    metric_data = query_result.raw_result
    
    # Verify the structure of the response
    assert isinstance(metric_data, dict), "metric_data should be a dictionary"
    print(f"Received metric data with keys: {list(metric_data.keys())}")
    
    # Verify required fields
    assert "Label" in metric_data, "Response should include a 'Label' field"
    assert "Timestamps" in metric_data, "Response should include 'Timestamps'"
    assert isinstance(metric_data["Timestamps"], list), "Timestamps should be a list"
    
    # Verify that statistics are included
    for stat in statistics:
        assert stat in metric_data, f"Response should include data for {stat} statistic"
        assert isinstance(metric_data[stat], list), f"{stat} data should be a list"
        assert len(metric_data[stat]) == len(metric_data["Timestamps"]), \
            f"Length of {stat} data ({len(metric_data[stat])}) should match number of timestamps ({len(metric_data['Timestamps'])})"
    
    # If we have data points, check their structure
    if len(metric_data["Timestamps"]) > 0:
        print(f"Retrieved {len(metric_data['Timestamps'])} data points")
        
        # Check timestamp order (should be ascending)
        for i in range(1, len(metric_data["Timestamps"])):
            assert metric_data["Timestamps"][i] > metric_data["Timestamps"][i-1], \
                "Timestamps should be in ascending order"
        
        # Check that timestamps are within the requested range
        start_timestamp = start_time.timestamp() * 1000  # Convert to milliseconds if needed
        end_timestamp = end_time.timestamp() * 1000      # Convert to milliseconds if needed
        
        for ts in metric_data["Timestamps"]:
            ts_value = ts
            if isinstance(ts, str):
                # If timestamp is a string, convert to timestamp
                ts_value = time.mktime(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").timetuple()) * 1000
            
            # Allow some flexibility in the time range due to API delays
            assert start_timestamp - 60000 <= ts_value <= end_timestamp + 60000, \
                f"Timestamp {ts} is outside the requested range"
        
        # Verify data point values
        for stat in statistics:
            for value in metric_data[stat]:
                assert isinstance(value, (int, float)) or value is None, \
                    f"Each {stat} value should be a number or None, got {type(value)}"
    else:
        print("No data points found for the specified time range")
    
    print(f"Successfully tested metric queries for CloudWatch metric: {namespace}:{metric_name}")
    
    return True