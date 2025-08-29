# 5-test_automation.py

async def test_automation(zerg_state=None):
    """Test Cortex XSOAR automation tasks and playbook execution"""
    print("Attempting to execute automation using Cortex XSOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    xsoar_server_url = zerg_state.get("xsoar_server_url").get("value")
    xsoar_api_key = zerg_state.get("xsoar_api_key").get("value")
    xsoar_api_key_id = zerg_state.get("xsoar_api_key_id").get("value")

    from connectors.xsoar.config import XSOARConnectorConfig
    from connectors.xsoar.connector import XSOARConnector
    from connectors.xsoar.tools import XSOARConnectorTools, ExecuteAutomationInput
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

    # grab the execute_automation tool and execute it
    execute_automation_tool = next(tool for tool in tools if tool.name == "execute_automation")
    automation_result = await execute_automation_tool.execute(
        script_name="Print",
        arguments={"value": "Test automation execution"}
    )
    automation_data = automation_result.result

    print("Type of returned automation_data:", type(automation_data))
    print(f"Automation execution result: {str(automation_data)[:200]}")

    # Verify that automation_data is a dictionary
    assert isinstance(automation_data, dict), "automation_data should be a dictionary"
    
    # Verify essential automation execution fields
    assert "Contents" in automation_data, "Automation result should have 'Contents' field"
    assert "Type" in automation_data, "Automation result should have 'Type' field"
    
    # Test playbook execution if available
    if "execute_playbook" in [tool.name for tool in tools]:
        execute_playbook_tool = next(tool for tool in tools if tool.name == "execute_playbook")
        playbook_result = await execute_playbook_tool.execute(
            playbook_id="test_playbook",
            incident_id="123"
        )
        playbook_data = playbook_result.result
        
        if playbook_data:
            assert isinstance(playbook_data, dict), "Playbook result should be a dictionary"
            
            playbook_fields = ["id", "name", "state", "startDate"]
            present_fields = [field for field in playbook_fields if field in playbook_data]
            
            print(f"Playbook execution contains these fields: {', '.join(present_fields)}")
    
    # Test task execution if available
    if "execute_task" in [tool.name for tool in tools]:
        execute_task_tool = next(tool for tool in tools if tool.name == "execute_task")
        task_result = await execute_task_tool.execute(
            task_id="test_task",
            parameters={"input": "test"}
        )
        task_data = task_result.result
        
        if task_data:
            assert isinstance(task_data, dict), "Task result should be a dictionary"
            print(f"Task execution completed successfully")

    print(f"Successfully executed automation tasks")

    return True