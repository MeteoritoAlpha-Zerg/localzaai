# 6-test_orchestration.py

async def test_orchestration(zerg_state=None):
    """Test Cortex XSOAR incident response workflow orchestration"""
    print("Attempting to manage incident response workflows using Cortex XSOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    xsoar_server_url = zerg_state.get("xsoar_server_url").get("value")
    xsoar_api_key = zerg_state.get("xsoar_api_key").get("value")
    xsoar_api_key_id = zerg_state.get("xsoar_api_key_id").get("value")

    from connectors.xsoar.config import XSOARConnectorConfig
    from connectors.xsoar.connector import XSOARConnector
    from connectors.xsoar.tools import XSOARConnectorTools, ManageWorkflowInput
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

    assert isinstance(team_selector.values, list), "team_selector values must be a list"
    team_id = team_selector.values[0] if team_selector.values else None
    print(f"Selecting investigation team ID: {team_id}")

    assert team_id, f"failed to retrieve investigation team ID from team selector"

    # set up the target with investigation team ID
    target = XSOARTarget(investigation_team_ids=[team_id])
    assert isinstance(target, ConnectorTargetInterface), "XSOARTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the manage_incident_workflow tool
    manage_workflow_tool = next(tool for tool in tools if tool.name == "manage_incident_workflow")
    
    # Test workflow management
    workflow_result = await manage_workflow_tool.execute(
        incident_id="123",
        action="assign",
        assignee="analyst@company.com"
    )
    workflow_data = workflow_result.result

    print("Type of returned workflow data:", type(workflow_data))
    print(f"Workflow management result: {str(workflow_data)[:200]}")

    # Verify that workflow_data is a dictionary
    assert isinstance(workflow_data, dict), "workflow_data should be a dictionary"
    
    # Verify workflow management fields
    assert "result" in workflow_data, "Workflow result should have 'result' field"
    assert "status" in workflow_data, "Workflow result should have 'status' field"
    
    # Test incident creation if available
    if "create_incident" in [tool.name for tool in tools]:
        create_incident_tool = next(tool for tool in tools if tool.name == "create_incident")
        incident_result = await create_incident_tool.execute(
            name="Test Security Incident",
            type="Malware",
            severity=3,
            details="Test incident for automation"
        )
        incident_data = incident_result.result
        
        if incident_data:
            assert isinstance(incident_data, dict), "Incident creation result should be a dictionary"
            assert "id" in incident_data, "Created incident should have 'id' field"
            
            print(f"Created incident with ID: {incident_data['id']}")
    
    # Test integration management if available
    if "manage_integrations" in [tool.name for tool in tools]:
        manage_integrations_tool = next(tool for tool in tools if tool.name == "manage_integrations")
        integrations_result = await manage_integrations_tool.execute(
            action="list_active"
        )
        integrations_data = integrations_result.result
        
        if integrations_data:
            assert isinstance(integrations_data, list), "Integrations data should be a list"
            
            if len(integrations_data) > 0:
                first_integration = integrations_data[0]
                assert "name" in first_integration, "Each integration should have 'name' field"
                
                print(f"Found {len(integrations_data)} active integrations")
    
    # Test workflow analytics if available
    if "get_workflow_analytics" in [tool.name for tool in tools]:
        get_analytics_tool = next(tool for tool in tools if tool.name == "get_workflow_analytics")
        analytics_result = await get_analytics_tool.execute(
            time_period="24h",
            team_id=team_id
        )
        analytics_data = analytics_result.result
        
        if analytics_data:
            assert isinstance(analytics_data, dict), "Analytics data should be a dictionary"
            
            analytics_fields = ["total_incidents", "avg_resolution_time", "automation_rate"]
            present_fields = [field for field in analytics_fields if field in analytics_data]
            
            print(f"Workflow analytics contains: {', '.join(present_fields)}")

    print(f"Successfully managed incident response workflows")

    return True