# 4-test_security_events.py

async def test_security_events(zerg_state=None):
    """Test OpenDNS security events enumeration by way of connector tools"""
    print("Attempting to retrieve OpenDNS security events using OpenDNS connector")

    assert zerg_state, "this test requires valid zerg_state"

    opendns_api_key = zerg_state.get("opendns_api_key").get("value")
    opendns_api_secret = zerg_state.get("opendns_api_secret").get("value")
    opendns_organization_id = zerg_state.get("opendns_organization_id").get("value")

    from connectors.opendns.config import OpenDNSConnectorConfig
    from connectors.opendns.connector import OpenDNSConnector
    from connectors.opendns.tools import OpenDNSConnectorTools
    from connectors.opendns.target import OpenDNSTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = OpenDNSConnectorConfig(
        api_key=opendns_api_key,
        api_secret=opendns_api_secret,
        organization_id=opendns_organization_id
    )
    assert isinstance(config, ConnectorConfig), "OpenDNSConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = OpenDNSConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "OpenDNSConnector should be of type Connector"

    # get query target options
    opendns_query_target_options = await connector.get_query_target_options()
    assert isinstance(opendns_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select organizations to target
    org_selector = None
    for selector in opendns_query_target_options.selectors:
        if selector.type == 'organization_ids':  
            org_selector = selector
            break

    assert org_selector, "failed to retrieve organization selector from query target options"

    # grab the first two organizations 
    num_orgs = 2
    assert isinstance(org_selector.values, list), "org_selector values must be a list"
    org_ids = org_selector.values[:num_orgs] if org_selector.values else None
    print(f"Selecting organization IDs: {org_ids}")

    assert org_ids, f"failed to retrieve {num_orgs} organization IDs from organization selector"

    # set up the target with organization IDs
    target = OpenDNSTarget(organization_ids=org_ids)
    assert isinstance(target, ConnectorTargetInterface), "OpenDNSTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_opendns_security_events tool
    opendns_get_security_events_tool = next(tool for tool in tools if tool.name == "get_opendns_security_events")
    opendns_security_events_result = await opendns_get_security_events_tool.execute()
    opendns_security_events = opendns_security_events_result.result

    print("Type of returned opendns_security_events:", type(opendns_security_events))
    print(f"len security events: {len(opendns_security_events)} events: {str(opendns_security_events)[:200]}")

    # Verify that opendns_security_events is a list
    assert isinstance(opendns_security_events, list), "opendns_security_events should be a list"
    assert len(opendns_security_events) > 0, "opendns_security_events should not be empty"
    
    # Verify structure of each security event object
    for event in opendns_security_events:
        assert "timestamp" in event, "Each security event should have a 'timestamp' field"
        assert "source" in event, "Each security event should have a 'source' field"
        assert "destination" in event, "Each security event should have a 'destination' field"
        
        # Verify essential OpenDNS security event fields
        assert "event_type" in event, "Each security event should have an 'event_type' field"
        assert "verdict" in event, "Each security event should have a 'verdict' field"
        assert "categories" in event, "Each security event should have a 'categories' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["policy_identity", "identity_types", "blocked_categories", "threat_types"]
        present_fields = [field for field in descriptive_fields if field in event]
        
        print(f"Security event {event.get('timestamp', 'unknown')} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first security event
        if event == opendns_security_events[0]:
            print(f"Example security event structure: {event}")

    print(f"Successfully retrieved and validated {len(opendns_security_events)} OpenDNS security events")

    return True