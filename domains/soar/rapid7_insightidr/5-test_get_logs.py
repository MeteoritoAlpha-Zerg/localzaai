# 5-test_get_logs.py

async def test_get_logs(zerg_state=None):
    """Test Rapid7 InsightIDR security logs retrieval"""
    print("Testing Rapid7 InsightIDR security logs retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    rapid7_insightidr_api_url = zerg_state.get("rapid7_insightidr_api_url").get("value")
    rapid7_insightidr_api_key = zerg_state.get("rapid7_insightidr_api_key").get("value")

    from connectors.rapid7_insightidr.config import Rapid7InsightIDRConnectorConfig
    from connectors.rapid7_insightidr.connector import Rapid7InsightIDRConnector
    from connectors.rapid7_insightidr.target import Rapid7InsightIDRTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = Rapid7InsightIDRConnectorConfig(
        api_url=rapid7_insightidr_api_url,
        api_key=rapid7_insightidr_api_key
    )
    assert isinstance(config, ConnectorConfig), "Rapid7InsightIDRConnectorConfig should be of type ConnectorConfig"

    connector = Rapid7InsightIDRConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "Rapid7InsightIDRConnector should be of type Connector"

    rapid7_insightidr_query_target_options = await connector.get_query_target_options()
    assert isinstance(rapid7_insightidr_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in rapid7_insightidr_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    logs_source = None
    for source in data_source_selector.values:
        if 'log' in source.lower():
            logs_source = source
            break
    
    assert logs_source, "Logs data source not found in available options"
    print(f"Selecting logs data source: {logs_source}")

    target = Rapid7InsightIDRTarget(data_sources=[logs_source])
    assert isinstance(target, ConnectorTargetInterface), "Rapid7InsightIDRTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_rapid7_insightidr_logs_tool = next(tool for tool in tools if tool.name == "get_rapid7_insightidr_logs")
    logs_result = await get_rapid7_insightidr_logs_tool.execute()
    logs_data = logs_result.result

    print("Type of returned logs data:", type(logs_data))
    print(f"Logs count: {len(logs_data)} sample: {str(logs_data)[:200]}")

    assert isinstance(logs_data, list), "Logs data should be a list"
    assert len(logs_data) > 0, "Logs data should not be empty"
    
    logs_to_check = logs_data[:10] if len(logs_data) > 10 else logs_data
    
    for log in logs_to_check:
        # Verify essential log fields
        assert "timestamp" in log, "Each log should have a 'timestamp' field"
        assert "log_source" in log, "Each log should have a 'log_source' field"
        assert "event_type" in log, "Each log should have an 'event_type' field"
        
        assert log["timestamp"], "Timestamp should not be empty"
        assert log["log_source"].strip(), "Log source should not be empty"
        assert log["event_type"].strip(), "Event type should not be empty"
        
        log_fields = ["message", "user", "source_ip", "destination_ip", "hostname", "raw_data"]
        present_fields = [field for field in log_fields if field in log]
        
        print(f"Log entry (type: {log['event_type']}, source: {log['log_source']}) contains: {', '.join(present_fields)}")
        
        # If source IP is present, validate it's not empty
        if "source_ip" in log:
            source_ip = log["source_ip"]
            assert source_ip and source_ip.strip(), "Source IP should not be empty"
        
        # If user is present, validate it's not empty
        if "user" in log:
            user = log["user"]
            assert user and user.strip(), "User should not be empty"
        
        # Log the structure of the first log entry for debugging
        if log == logs_to_check[0]:
            print(f"Example log structure: {log}")

    print(f"Successfully retrieved and validated {len(logs_data)} Rapid7 InsightIDR logs")

    return True