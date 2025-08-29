# 4-test_incidents.py

async def test_incidents(zerg_state=None):
    """Test Cortex XSOAR incidents enumeration by way of connector tools"""
    print("Attempting to retrieve Cortex XSOAR incidents using XSOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    xsoar_server_url = zerg_state.get("xsoar_server_url").get("value")
    xsoar_api_key = zerg_state.get("xsoar_api_key").get("value")
    xsoar_api_key_id = zerg_state.get("xsoar_api_key_id").get("value")

    from connectors.xsoar.config import XSOARConnectorConfig
    from connectors.xsoar.connector import XSOARConnector
    from connectors.xsoar.tools import XSOARConnectorTools
    from connectors.xsoar.target import XSOARTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = XSOARConnectorConfig(
        server_url=xsoar_server_url,
        api_key=xsoar_api_key,
        api_key_id=xsoar_api_key_id
    )
    assert isinstance(config, ConnectorConfig), "XSOARConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = XSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "XSOARConnector should be of type Connector"

    # get query target options
    xsoar_query_target_options = await connector.get_query_target_options()
    assert isinstance(xsoar_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select investigation teams to target
    team_selector = None
    for selector in xsoar_query_target_options.selectors:
        if selector.type == 'investigation_team_ids':  
            team_selector = selector
            break

    assert team_selector, "failed to retrieve investigation team selector from query target options"

    # grab the first two investigation teams 
    num_teams = 2
    assert isinstance(team_selector.values, list), "team_selector values must be a list"
    team_ids = team_selector.values[:num_teams] if team_selector.values else None
    print(f"Selecting investigation team IDs: {team_ids}")

    assert team_ids, f"failed to retrieve {num_teams} investigation team IDs from team selector"

    # set up the target with investigation team IDs
    target = XSOARTarget(investigation_team_ids=team_ids)
    assert isinstance(target, ConnectorTargetInterface), "XSOARTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_xsoar_incidents tool
    xsoar_get_incidents_tool = next(tool for tool in tools if tool.name == "get_xsoar_incidents")
    xsoar_incidents_result = await xsoar_get_incidents_tool.execute()
    xsoar_incidents = xsoar_incidents_result.result

    print("Type of returned xsoar_incidents:", type(xsoar_incidents))
    print(f"len incidents: {len(xsoar_incidents)} incidents: {str(xsoar_incidents)[:200]}")

    # Verify that xsoar_incidents is a list
    assert isinstance(xsoar_incidents, list), "xsoar_incidents should be a list"
    assert len(xsoar_incidents) > 0, "xsoar_incidents should not be empty"
    
    # Verify structure of each incident object
    for incident in xsoar_incidents:
        assert "id" in incident, "Each incident should have an 'id' field"
        assert "name" in incident, "Each incident should have a 'name' field"
        assert "status" in incident, "Each incident should have a 'status' field"
        assert "severity" in incident, "Each incident should have a 'severity' field"
        assert "created" in incident, "Each incident should have a 'created' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["owner", "type", "labels", "playbookId"]
        present_fields = [field for field in descriptive_fields if field in incident]
        
        print(f"Incident {incident['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first incident
        if incident == xsoar_incidents[0]:
            print(f"Example incident structure: {incident}")

    print(f"Successfully retrieved and validated {len(xsoar_incidents)} Cortex XSOAR incidents")

    return True