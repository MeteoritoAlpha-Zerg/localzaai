# 4-test_list_events.py

async def test_list_events(zerg_state=None):
    """Test MISP events enumeration by way of connector tools"""
    print("Attempting to retrieve MISP events using MISP connector")

    assert zerg_state, "this test requires valid zerg_state"

    misp_url = zerg_state.get("misp_url").get("value")
    misp_api_key = zerg_state.get("misp_api_key").get("value")

    from connectors.misp.config import MISPConnectorConfig
    from connectors.misp.connector import MISPConnector
    from connectors.misp.tools import MISPConnectorTools
    from connectors.misp.target import MISPTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = MISPConnectorConfig(
        url=misp_url,
        api_key=misp_api_key
    )
    assert isinstance(config, ConnectorConfig), "MISPConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = MISPConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MISPConnector should be of type Connector"

    # get query target options
    misp_query_target_options = await connector.get_query_target_options()
    assert isinstance(misp_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select organizations to target
    org_selector = None
    for selector in misp_query_target_options.selectors:
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
    target = MISPTarget(organization_ids=org_ids)
    assert isinstance(target, ConnectorTargetInterface), "MISPTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_misp_events tool
    misp_get_events_tool = next(tool for tool in tools if tool.name == "get_misp_events")
    misp_events_result = await misp_get_events_tool.execute()
    misp_events = misp_events_result.result

    print("Type of returned misp_events:", type(misp_events))
    print(f"len events: {len(misp_events)} events: {str(misp_events)[:200]}")

    # Verify that misp_events is a list
    assert isinstance(misp_events, list), "misp_events should be a list"
    assert len(misp_events) > 0, "misp_events should not be empty"
    
    # Verify structure of each event object
    for event in misp_events:
        assert "id" in event, "Each event should have an 'id' field"
        assert "uuid" in event, "Each event should have a 'uuid' field"
        assert "info" in event, "Each event should have an 'info' field"
        
        # Verify essential MISP event fields
        assert "date" in event, "Each event should have a 'date' field"
        assert "threat_level_id" in event, "Each event should have a 'threat_level_id' field"
        assert "analysis" in event, "Each event should have an 'analysis' field"
        assert "orgc_id" in event, "Each event should have an 'orgc_id' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["attribute_count", "distribution", "sharing_group_id", "timestamp"]
        present_fields = [field for field in descriptive_fields if field in event]
        
        print(f"Event {event['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first event
        if event == misp_events[0]:
            print(f"Example event structure: {event}")

    print(f"Successfully retrieved and validated {len(misp_events)} MISP events")

    return True