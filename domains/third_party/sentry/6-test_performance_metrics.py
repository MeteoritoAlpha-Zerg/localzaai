# 6-test_performance_metrics.py

async def test_performance_metrics(zerg_state=None):
    """Test Sentry performance metrics and event data analysis"""
    print("Testing Sentry performance metrics and event data analysis")

    assert zerg_state, "this test requires valid zerg_state"

    sentry_api_token = zerg_state.get("sentry_api_token").get("value")
    sentry_organization_slug = zerg_state.get("sentry_organization_slug").get("value")
    sentry_base_url = zerg_state.get("sentry_base_url").get("value")

    from connectors.sentry.config import SentryConnectorConfig
    from connectors.sentry.connector import SentryConnector
    from connectors.sentry.target import SentryTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = SentryConnectorConfig(
        api_token=sentry_api_token,
        organization_slug=sentry_organization_slug,
        base_url=sentry_base_url
    )
    assert isinstance(config, ConnectorConfig), "SentryConnectorConfig should be of type ConnectorConfig"

    connector = SentryConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SentryConnector should be of type Connector"

    sentry_query_target_options = await connector.get_query_target_options()
    assert isinstance(sentry_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    project_selector = None
    for selector in sentry_query_target_options.selectors:
        if selector.type == 'project_slugs':  
            project_selector = selector
            break

    assert project_selector, "failed to retrieve project selector from query target options"

    assert isinstance(project_selector.values, list), "project_selector values must be a list"
    project_slug = project_selector.values[0] if project_selector.values else None
    print(f"Using project for performance metrics analysis: {project_slug}")

    assert project_slug, f"failed to retrieve project slug from project selector"

    target = SentryTarget(project_slugs=[project_slug])
    assert isinstance(target, ConnectorTargetInterface), "SentryTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_performance_metrics_tool = next(tool for tool in tools if tool.name == "get_performance_metrics")
    
    performance_result = await get_performance_metrics_tool.execute(
        project_slug=project_slug,
        time_window_hours=24
    )
    performance_metrics = performance_result.result

    print("Type of returned performance_metrics:", type(performance_metrics))
    print(f"Performance metrics preview: {str(performance_metrics)[:200]}")

    assert performance_metrics is not None, "performance_metrics should not be None"
    
    if isinstance(performance_metrics, dict):
        expected_fields = ["project_slug", "transactions", "metrics", "releases", "stats"]
        present_fields = [field for field in expected_fields if field in performance_metrics]
        
        if len(present_fields) > 0:
            print(f"Performance metrics contains these fields: {', '.join(present_fields)}")
            
            if "metrics" in performance_metrics:
                metrics = performance_metrics["metrics"]
                assert isinstance(metrics, dict), "Metrics should be a dictionary"
                
                metric_fields = ["throughput", "apdex", "p95", "error_rate"]
                present_metrics = [field for field in metric_fields if field in metrics]
                print(f"Metrics contain: {', '.join(present_metrics)}")
            
            if "transactions" in performance_metrics:
                transactions = performance_metrics["transactions"]
                assert isinstance(transactions, list), "Transactions should be a list"
                print(f"Found {len(transactions)} transactions")
            
            if "releases" in performance_metrics:
                releases = performance_metrics["releases"]
                assert isinstance(releases, list), "Releases should be a list"
                print(f"Found {len(releases)} releases")
        
        print(f"Performance metrics structure: {performance_metrics}")
        
    elif isinstance(performance_metrics, list):
        assert len(performance_metrics) > 0, "Performance metrics list should not be empty"
        
        sample_item = performance_metrics[0]
        assert isinstance(sample_item, dict), "Performance metric items should be dictionaries"
        
        item_fields = ["transaction", "duration", "timestamp", "user", "tags"]
        present_item_fields = [field for field in item_fields if field in sample_item]
        
        print(f"Performance metric items contain these fields: {', '.join(present_item_fields)}")
        
        if "duration" in sample_item:
            duration = sample_item["duration"]
            assert isinstance(duration, (int, float)), "Duration should be numeric"
        
        print(f"Example performance metric item: {sample_item}")
        
    else:
        assert str(performance_metrics).strip() != "", "Performance metrics should contain meaningful data"

    print(f"Successfully retrieved and validated performance metrics data")

    return True