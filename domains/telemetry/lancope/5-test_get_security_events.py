# 5-test_get_security_events.py

async def test_get_security_events(zerg_state=None):
    """Test Cisco Stealthwatch security events retrieval"""
    print("Testing Cisco Stealthwatch security events retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    cisco_stealthwatch_api_url = zerg_state.get("cisco_stealthwatch_api_url").get("value")
    cisco_stealthwatch_username = zerg_state.get("cisco_stealthwatch_username").get("value")
    cisco_stealthwatch_password = zerg_state.get("cisco_stealthwatch_password").get("value")

    from connectors.cisco_stealthwatch.config import CiscoStealthwatchConnectorConfig
    from connectors.cisco_stealthwatch.connector import CiscoStealthwatchConnector
    from connectors.cisco_stealthwatch.target import CiscoStealthwatchTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = CiscoStealthwatchConnectorConfig(
        api_url=cisco_stealthwatch_api_url,
        username=cisco_stealthwatch_username,
        password=cisco_stealthwatch_password
    )
    assert isinstance(config, ConnectorConfig), "CiscoStealthwatchConnectorConfig should be of type ConnectorConfig"

    connector = CiscoStealthwatchConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CiscoStealthwatchConnector should be of type Connector"

    cisco_stealthwatch_query_target_options = await connector.get_query_target_options()
    assert isinstance(cisco_stealthwatch_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in cisco_stealthwatch_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    security_events_source = None
    for source in data_source_selector.values:
        if 'security_event' in source.lower() or 'event' in source.lower():
            security_events_source = source
            break
    
    assert security_events_source, "Security events data source not found in available options"
    print(f"Selecting security events data source: {security_events_source}")

    target = CiscoStealthwatchTarget(data_sources=[security_events_source])
    assert isinstance(target, ConnectorTargetInterface), "CiscoStealthwatchTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_cisco_stealthwatch_security_events_tool = next(tool for tool in tools if tool.name == "get_cisco_stealthwatch_security_events")
    security_events_result = await get_cisco_stealthwatch_security_events_tool.execute()
    security_events_data = security_events_result.result

    print("Type of returned security events data:", type(security_events_data))
    print(f"Security events count: {len(security_events_data)} sample: {str(security_events_data)[:200]}")

    assert isinstance(security_events_data, list), "Security events data should be a list"
    assert len(security_events_data) > 0, "Security events data should not be empty"
    
    events_to_check = security_events_data[:10] if len(security_events_data) > 10 else security_events_data
    
    for event in events_to_check:
        # Verify essential security event fields per Cisco Stealthwatch API specification
        assert "id" in event, "Each security event should have an 'id' field"
        assert "type" in event, "Each security event should have a 'type' field"
        assert "timestamp" in event, "Each security event should have a 'timestamp' field"
        assert "severity" in event, "Each security event should have a 'severity' field"
        
        assert event["id"], "Security event ID should not be empty"
        assert event["type"].strip(), "Security event type should not be empty"
        assert event["timestamp"], "Timestamp should not be empty"
        
        # Verify severity is valid
        valid_severities = ["low", "medium", "high", "critical"]
        severity = event["severity"].lower()
        assert severity in valid_severities, f"Invalid severity level: {severity}"
        
        event_fields = ["source_ip", "destination_ip", "description", "policy_name", "confidence", "threat_name"]
        present_fields = [field for field in event_fields if field in event]
        
        print(f"Security event {event['id']} (type: {event['type']}, severity: {event['severity']}) contains: {', '.join(present_fields)}")
        
        # If source IP is present, validate it's not empty
        if "source_ip" in event:
            source_ip = event["source_ip"]
            assert source_ip and source_ip.strip(), "Source IP should not be empty"
        
        # If destination IP is present, validate it's not empty
        if "destination_ip" in event:
            dest_ip = event["destination_ip"]
            assert dest_ip and dest_ip.strip(), "Destination IP should not be empty"
        
        # If confidence is present, validate it's numeric
        if "confidence" in event:
            confidence = event["confidence"]
            assert isinstance(confidence, (int, float)), "Confidence should be numeric"
            assert 0 <= confidence <= 100, f"Confidence should be between 0 and 100: {confidence}"
        
        # If description is present, validate it's not empty
        if "description" in event:
            description = event["description"]
            assert description and description.strip(), "Description should not be empty"
        
        # Log the structure of the first security event for debugging
        if event == events_to_check[0]:
            print(f"Example security event structure: {event}")

    print(f"Successfully retrieved and validated {len(security_events_data)} Cisco Stealthwatch security events")

    return True