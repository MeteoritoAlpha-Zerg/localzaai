# 4-test_security_events.py

async def test_security_events(zerg_state=None):
    """Test Google Chronicle security events enumeration by way of connector tools"""
    print("Attempting to retrieve Google Chronicle security events using Chronicle connector")

    assert zerg_state, "this test requires valid zerg_state"

    chronicle_service_account_path = zerg_state.get("chronicle_service_account_path").get("value")
    chronicle_customer_id = zerg_state.get("chronicle_customer_id").get("value")

    from connectors.chronicle.config import ChronicleConnectorConfig
    from connectors.chronicle.connector import ChronicleConnector
    from connectors.chronicle.tools import ChronicleConnectorTools
    from connectors.chronicle.target import ChronicleTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = ChronicleConnectorConfig(
        service_account_path=chronicle_service_account_path,
        customer_id=chronicle_customer_id
    )
    assert isinstance(config, ConnectorConfig), "ChronicleConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ChronicleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ChronicleConnector should be of type Connector"

    # get query target options
    chronicle_query_target_options = await connector.get_query_target_options()
    assert isinstance(chronicle_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select data sources to target
    data_source_selector = None
    for selector in chronicle_query_target_options.selectors:
        if selector.type == 'data_source_ids':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"

    # grab the first two data sources 
    num_sources = 2
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    data_source_ids = data_source_selector.values[:num_sources] if data_source_selector.values else None
    print(f"Selecting data source IDs: {data_source_ids}")

    assert data_source_ids, f"failed to retrieve {num_sources} data source IDs from data source selector"

    # set up the target with data source IDs
    target = ChronicleTarget(data_source_ids=data_source_ids)
    assert isinstance(target, ConnectorTargetInterface), "ChronicleTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_chronicle_events tool
    chronicle_get_events_tool = next(tool for tool in tools if tool.name == "get_chronicle_events")
    chronicle_events_result = await chronicle_get_events_tool.execute()
    chronicle_events = chronicle_events_result.result

    print("Type of returned chronicle_events:", type(chronicle_events))
    print(f"len security events: {len(chronicle_events)} events: {str(chronicle_events)[:200]}")

    # Verify that chronicle_events is a list
    assert isinstance(chronicle_events, list), "chronicle_events should be a list"
    assert len(chronicle_events) > 0, "chronicle_events should not be empty"
    
    # Verify structure of each security event object
    for event in chronicle_events:
        assert "metadata" in event, "Each security event should have a 'metadata' field"
        assert "principal" in event or "target" in event or "src" in event, "Each security event should have principal, target, or src field"
        
        metadata = event["metadata"]
        
        # Verify essential Chronicle UDM event fields
        assert "event_timestamp" in metadata, "Event metadata should have an 'event_timestamp' field"
        assert "event_type" in metadata, "Event metadata should have an 'event_type' field"
        assert "product_name" in metadata, "Event metadata should have a 'product_name' field"
        assert "vendor_name" in metadata, "Event metadata should have a 'vendor_name' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["description", "product_event_type", "product_log_id", "ingested_timestamp"]
        present_fields = [field for field in descriptive_fields if field in metadata]
        
        print(f"Security event {metadata.get('product_log_id', 'unknown')} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first security event
        if event == chronicle_events[0]:
            print(f"Example security event structure: {event}")

    print(f"Successfully retrieved and validated {len(chronicle_events)} Google Chronicle security events")

    return True