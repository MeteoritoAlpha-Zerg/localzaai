# 4-test_list_metrics.py

async def test_list_metrics(zerg_state=None):
    """Test CloudWatch metrics enumeration through connector tools"""
    print("Attempting to authenticate using CloudWatch connector")

    assert zerg_state, "this test requires valid zerg_state"

    aws_region = zerg_state.get("aws_region").get("value")
    aws_access_key_id = zerg_state.get("aws_access_key_id").get("value")
    aws_secret_access_key = zerg_state.get("aws_secret_access_key").get("value")
    aws_session_token = zerg_state.get("aws_session_token", {}).get("value")

    from connectors.cloudwatch.config import CloudWatchConnectorConfig
    from connectors.cloudwatch.connector import CloudWatchConnector
    from connectors.cloudwatch.tools import CloudWatchConnectorTools
    from connectors.cloudwatch.target import CloudWatchTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

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

    # find the get_cloudwatch_metrics tool and execute it
    get_metrics_tool = next((tool for tool in tools if tool.name == "get_cloudwatch_metrics"), None)
    assert get_metrics_tool, "get_cloudwatch_metrics tool not found in available tools"
    
    metrics_result = await get_metrics_tool.execute()
    metrics = metrics_result.raw_result

    print("Type of returned metrics:", type(metrics))
    print(f"Number of metric namespaces: {len(metrics)}")
    
    # Verify that metrics is a dictionary of namespaces
    assert isinstance(metrics, dict), "metrics should be a dictionary of namespaces"
    assert len(metrics) > 0, "metrics should not be empty"
    
    # Check the structure of the metrics dictionary
    # It should be a dict where keys are namespace names and values are lists of metrics
    for namespace, namespace_metrics in metrics.items():
        print(f"Namespace: {namespace}, Metrics count: {len(namespace_metrics)}")
        assert isinstance(namespace, str), "Namespace key should be a string"
        assert isinstance(namespace_metrics, list), f"Metrics for namespace {namespace} should be a list"
        
        # Check structure of some metrics from each namespace
        metrics_to_check = namespace_metrics[:3] if len(namespace_metrics) > 3 else namespace_metrics
        
        for metric in metrics_to_check:
            # Verify essential metric fields
            assert "MetricName" in metric, "Each metric should have a 'MetricName' field"
            assert "Namespace" in metric, "Each metric should have a 'Namespace' field"
            
            # Verify namespace field matches the key
            assert metric["Namespace"] == namespace, f"Metric namespace {metric['Namespace']} does not match key {namespace}"
            
            # Check for dimensions (optional but common)
            if "Dimensions" in metric:
                assert isinstance(metric["Dimensions"], list), "Dimensions should be a list"
                for dimension in metric["Dimensions"]:
                    assert "Name" in dimension, "Each dimension should have a 'Name' field"
                    assert "Value" in dimension, "Each dimension should have a 'Value' field"
            
            print(f"  - {metric['MetricName']}")
        
        # Log the structure of the first metric for debugging
        if namespace_metrics and namespace == list(metrics.keys())[0]:
            print(f"Example metric structure: {namespace_metrics[0]}")

    print(f"Successfully retrieved and validated CloudWatch metrics from {len(metrics)} namespaces")

    return True