# 4-test_security_events.py

async def test_security_events(zerg_state=None):
    """Test ArcSight security events enumeration by way of connector tools"""
    print("Attempting to retrieve ArcSight security events using ArcSight connector")

    assert zerg_state, "this test requires valid zerg_state"

    arcsight_server_url = zerg_state.get("arcsight_server_url").get("value")
    arcsight_username = zerg_state.get("arcsight_username").get("value")
    arcsight_password = zerg_state.get("arcsight_password").get("value")

    from connectors.arcsight.config import ArcSightConnectorConfig
    from connectors.arcsight.connector import ArcSightConnector
    from connectors.arcsight.tools import ArcSightConnectorTools
    from connectors.arcsight.target import ArcSightTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = ArcSightConnectorConfig(
        server_url=arcsight_server_url,
        username=arcsight_username,
        password=arcsight_password
    )
    assert isinstance(config, ConnectorConfig), "ArcSightConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ArcSightConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ArcSightConnector should be of type Connector"

    # get query target options
    arcsight_query_target_options = await connector.get_query_target_options()
    assert isinstance(arcsight_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select security managers to target
    security_manager_selector = None
    for selector in arcsight_query_target_options.selectors:
        if selector.type == 'security_manager_ids':  
            security_manager_selector = selector
            break

    assert security_manager_selector, "failed to retrieve security manager selector from query target options"

    # grab the first two security managers 
    num_managers = 2
    assert isinstance(security_manager_selector.values, list), "security_manager_selector values must be a list"
    security_manager_ids = security_manager_selector.values[:num_managers] if security_manager_selector.values else None
    print(f"Selecting security manager IDs: {security_manager_ids}")

    assert security_manager_ids, f"failed to retrieve {num_managers} security manager IDs from security manager selector"

    # set up the target with security manager IDs
    target = ArcSightTarget(security_manager_ids=security_manager_ids)
    assert isinstance(target, ConnectorTargetInterface), "ArcSightTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_arcsight_events tool
    arcsight_get_events_tool = next(tool for tool in tools if tool.name == "get_arcsight_events")
    arcsight_events_result = await arcsight_get_events_tool.execute()
    arcsight_events = arcsight_events_result.result

    print("Type of returned arcsight_events:", type(arcsight_events))
    print(f"len security events: {len(arcsight_events)} events: {str(arcsight_events)[:200]}")

    # Verify that arcsight_events is a list
    assert isinstance(arcsight_events, list), "arcsight_events should be a list"
    assert len(arcsight_events) > 0, "arcsight_events should not be empty"
    
    # Verify structure of each security event object
    for event in arcsight_events:
        assert "eventId" in event, "Each security event should have an 'eventId' field"
        assert "baseEventIds" in event, "Each security event should have a 'baseEventIds' field"
        assert "startTime" in event, "Each security event should have a 'startTime' field"
        
        # Verify essential ArcSight security event fields
        assert "name" in event, "Each security event should have a 'name' field"
        assert "type" in event, "Each security event should have a 'type' field"
        assert "deviceEventClassId" in event, "Each security event should have a 'deviceEventClassId' field"
        assert "priority" in event, "Each security event should have a 'priority' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["sourceAddress", "destinationAddress", "deviceVendor", "deviceProduct", "managerReceiptTime"]
        present_fields = [field for field in descriptive_fields if field in event]
        
        print(f"Security event {event['eventId']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first security event
        if event == arcsight_events[0]:
            print(f"Example security event structure: {event}")

    print(f"Successfully retrieved and validated {len(arcsight_events)} ArcSight security events")

    return True