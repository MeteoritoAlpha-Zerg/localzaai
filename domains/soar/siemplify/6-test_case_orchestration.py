# 6-test_case_orchestration.py

async def test_case_orchestration(zerg_state=None):
    """Test Siemplify case workflow orchestration"""
    print("Attempting to manage case workflows using Siemplify connector")

    assert zerg_state, "this test requires valid zerg_state"

    siemplify_server_url = zerg_state.get("siemplify_server_url").get("value")
    siemplify_api_token = zerg_state.get("siemplify_api_token").get("value")
    siemplify_user_name = zerg_state.get("siemplify_user_name").get("value")

    from connectors.siemplify.config import SimemplifyConnectorConfig
    from connectors.siemplify.connector import SimemplifyConnector
    from connectors.siemplify.tools import SimemplifyConnectorTools, ManageCaseWorkflowInput
    from connectors.siemplify.target import SimemplifyTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SimemplifyConnectorConfig(
        server_url=siemplify_server_url,
        api_token=siemplify_api_token,
        user_name=siemplify_user_name
    )
    assert isinstance(config, ConnectorConfig), "SimemplifyConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SimemplifyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SimemplifyConnector should be of type Connector"

    # get query target options
    siemplify_query_target_options = await connector.get_query_target_options()
    assert isinstance(siemplify_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select environments to target
    environment_selector = None
    for selector in siemplify_query_target_options.selectors:
        if selector.type == 'environment_ids':  
            environment_selector = selector
            break

    assert environment_selector, "failed to retrieve environment selector from query target options"

    assert isinstance(environment_selector.values, list), "environment_selector values must be a list"
    environment_id = environment_selector.values[0] if environment_selector.values else None
    print(f"Selecting environment ID: {environment_id}")

    assert environment_id, f"failed to retrieve environment ID from environment selector"

    # set up the target with environment ID
    target = SimemplifyTarget(environment_ids=[environment_id])
    assert isinstance(target, ConnectorTargetInterface), "SimemplifyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the manage_case_workflow tool
    manage_workflow_tool = next(tool for tool in tools if tool.name == "manage_case_workflow")
    
    # Test workflow management
    workflow_result = await manage_workflow_tool.execute(
        case_id="12345",
        action="assign",
        assignee="analyst@company.com"
    )
    workflow_data = workflow_result.result

    print("Type of returned workflow data:", type(workflow_data))
    print(f"Workflow management result: {str(workflow_data)[:200]}")

    # Verify that workflow_data is a dictionary
    assert isinstance(workflow_data, dict), "workflow_data should be a dictionary"
    
    # Verify workflow management fields
    assert "success" in workflow_data, "Workflow result should have 'success' field"
    assert "case_id" in workflow_data, "Workflow result should have 'case_id' field"
    
    # Test case creation if available
    if "create_case" in [tool.name for tool in tools]:
        create_case_tool = next(tool for tool in tools if tool.name == "create_case")
        case_result = await create_case_tool.execute(
            title="Test Security Case",
            environment=environment_id,
            priority=3,
            description="Test case for automation"
        )
        case_data = case_result.result
        
        if case_data:
            assert isinstance(case_data, dict), "Case creation result should be a dictionary"
            assert "identifier" in case_data, "Created case should have 'identifier' field"
            
            print(f"Created case with ID: {case_data['identifier']}")
    
    # Test alert management if available
    if "manage_alerts" in [tool.name for tool in tools]:
        manage_alerts_tool = next(tool for tool in tools if tool.name == "manage_alerts")
        alerts_result = await manage_alerts_tool.execute(
            case_id="12345",
            action="escalate"
        )
        alerts_data = alerts_result.result
        
        if alerts_data:
            assert isinstance(alerts_data, dict), "Alerts management result should be a dictionary"
            print(f"Alert management action completed")
    
    # Test case analytics if available
    if "get_case_analytics" in [tool.name for tool in tools]:
        get_analytics_tool = next(tool for tool in tools if tool.name == "get_case_analytics")
        analytics_result = await get_analytics_tool.execute(
            environment_id=environment_id,
            time_period="24h"
        )
        analytics_data = analytics_result.result
        
        if analytics_data:
            assert isinstance(analytics_data, dict), "Analytics data should be a dictionary"
            
            analytics_fields = ["total_cases", "avg_resolution_time", "automation_rate"]
            present_fields = [field for field in analytics_fields if field in analytics_data]
            
            print(f"Case analytics contains: {', '.join(present_fields)}")

    print(f"Successfully managed case workflows and orchestration")

    return True