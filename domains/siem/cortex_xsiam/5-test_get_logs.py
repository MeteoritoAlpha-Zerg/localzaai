# 5-test_get_logs.py

async def test_get_logs(zerg_state=None):
    """Test Cortex XSIAM security logs retrieval"""
    print("Testing Cortex XSIAM security logs retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    cortex_xsiam_api_url = zerg_state.get("cortex_xsiam_api_url").get("value")
    cortex_xsiam_api_key = zerg_state.get("cortex_xsiam_api_key").get("value")
    cortex_xsiam_api_key_id = zerg_state.get("cortex_xsiam_api_key_id").get("value")
    cortex_xsiam_tenant_id = zerg_state.get("cortex_xsiam_tenant_id").get("value")

    from connectors.cortex_xsiam.config import CortexXSIAMConnectorConfig
    from connectors.cortex_xsiam.connector import CortexXSIAMConnector
    from connectors.cortex_xsiam.target import CortexXSIAMTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = CortexXSIAMConnectorConfig(
        api_url=cortex_xsiam_api_url,
        api_key=cortex_xsiam_api_key,
        api_key_id=cortex_xsiam_api_key_id,
        tenant_id=cortex_xsiam_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "CortexXSIAMConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CortexXSIAMConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CortexXSIAMConnector should be of type Connector"

    # get query target options
    cortex_xsiam_query_target_options = await connector.get_query_target_options()
    assert isinstance(cortex_xsiam_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select logs data source
    data_source_selector = None
    for selector in cortex_xsiam_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find logs in available data sources
    logs_source = None
    for source in data_source_selector.values:
        if 'log' in source.lower():
            logs_source = source
            break
    
    assert logs_source, "Logs data source not found in available options"
    print(f"Selecting logs data source: {logs_source}")

    # set up the target with logs data source
    target = CortexXSIAMTarget(data_sources=[logs_source])
    assert isinstance(target, ConnectorTargetInterface), "CortexXSIAMTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_cortex_xsiam_logs tool and execute it
    get_cortex_xsiam_logs_tool = next(tool for tool in tools if tool.name == "get_cortex_xsiam_logs")
    logs_result = await get_cortex_xsiam_logs_tool.execute()
    logs_data = logs_result.result

    print("Type of returned logs data:", type(logs_data))
    print(f"Logs count: {len(logs_data)} sample: {str(logs_data)[:200]}")

    # Verify that logs_data is a list
    assert isinstance(logs_data, list), "Logs data should be a list"
    assert len(logs_data) > 0, "Logs data should not be empty"
    
    # Limit the number of logs to check if there are many
    logs_to_check = logs_data[:10] if len(logs_data) > 10 else logs_data
    
    # Verify structure of each log entry
    for log in logs_to_check:
        # Verify essential log fields
        assert "timestamp" in log, "Each log should have a 'timestamp' field"
        assert "event_type" in log, "Each log should have an 'event_type' field"
        assert "source" in log, "Each log should have a 'source' field"
        
        # Verify timestamp is not empty
        assert log["timestamp"], "Timestamp should not be empty"
        
        # Verify event type is not empty
        assert log["event_type"].strip(), "Event type should not be empty"
        
        # Verify source is not empty
        assert log["source"].strip(), "Source should not be empty"
        
        # Check for additional log fields
        log_fields = ["message", "level", "host", "user", "action", "result", "raw_data", "normalized_fields"]
        present_fields = [field for field in log_fields if field in log]
        
        print(f"Log entry (type: {log['event_type']}, source: {log['source']}) contains: {', '.join(present_fields)}")
        
        # If level is present, validate it's a valid log level
        if "level" in log:
            level = log["level"].lower()
            valid_levels = ["debug", "info", "warn", "warning", "error", "critical", "fatal"]
            assert any(valid_level in level for valid_level in valid_levels), f"Invalid log level: {level}"
        
        # If host is present, validate it's not empty
        if "host" in log:
            host = log["host"]
            assert host and host.strip(), "Host should not be empty"
        
        # If user is present, validate it's not empty
        if "user" in log:
            user = log["user"]
            assert user and user.strip(), "User should not be empty"
        
        # If action is present, validate it's not empty
        if "action" in log:
            action = log["action"]
            assert action and action.strip(), "Action should not be empty"
        
        # If result is present, validate it's not empty
        if "result" in log:
            result = log["result"]
            assert result and result.strip(), "Result should not be empty"
        
        # If normalized fields are present, validate structure
        if "normalized_fields" in log:
            normalized_fields = log["normalized_fields"]
            assert isinstance(normalized_fields, dict), "Normalized fields should be a dictionary"
        
        # Log the structure of the first log entry for debugging
        if log == logs_to_check[0]:
            print(f"Example log structure: {log}")

    print(f"Successfully retrieved and validated {len(logs_data)} Cortex XSIAM logs")

    return True