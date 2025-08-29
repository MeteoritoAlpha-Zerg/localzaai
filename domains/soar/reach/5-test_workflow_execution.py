# 5-test_workflow_execution.py

async def test_workflow_execution(zerg_state=None):
    """Test Reach SOAR workflow execution"""
    print("Testing Reach SOAR workflow execution")

    assert zerg_state, "this test requires valid zerg_state"

    reach_soar_api_token = zerg_state.get("reach_soar_api_token").get("value")
    reach_soar_base_url = zerg_state.get("reach_soar_base_url").get("value")
    reach_soar_tenant_id = zerg_state.get("reach_soar_tenant_id").get("value")

    from connectors.reach_soar.config import ReachSOARConnectorConfig
    from connectors.reach_soar.connector import ReachSOARConnector
    from connectors.reach_soar.target import ReachSOARTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = ReachSOARConnectorConfig(
        api_token=reach_soar_api_token,
        base_url=reach_soar_base_url,
        tenant_id=reach_soar_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "ReachSOARConnectorConfig should be of type ConnectorConfig"

    connector = ReachSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ReachSOARConnector should be of type Connector"

    reach_soar_query_target_options = await connector.get_query_target_options()
    assert isinstance(reach_soar_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    workflow_selector = None
    for selector in reach_soar_query_target_options.selectors:
        if selector.type == 'workflow_ids':  
            workflow_selector = selector
            break

    assert workflow_selector, "failed to retrieve workflow selector from query target options"

    assert isinstance(workflow_selector.values, list), "workflow_selector values must be a list"
    workflow_id = workflow_selector.values[0] if workflow_selector.values else None
    print(f"Selecting workflow ID: {workflow_id}")

    assert workflow_id, f"failed to retrieve workflow ID from workflow selector"

    target = ReachSOARTarget(workflow_ids=[workflow_id])
    assert isinstance(target, ConnectorTargetInterface), "ReachSOARTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    execute_workflow_tool = next(tool for tool in tools if tool.name == "execute_workflow")
    
    test_workflow_params = {
        "incident_id": "test-incident-001",
        "priority": "medium",
        "source": "connector_test"
    }
    
    execution_result = await execute_workflow_tool.execute(
        workflow_id=workflow_id,
        parameters=test_workflow_params
    )
    workflow_execution = execution_result.result

    print("Type of returned workflow_execution:", type(workflow_execution))
    print(f"Workflow execution preview: {str(workflow_execution)[:200]}")

    assert workflow_execution is not None, "workflow_execution should not be None"
    
    if isinstance(workflow_execution, dict):
        expected_fields = ["execution_id", "status", "workflow_id", "start_time", "result"]
        present_fields = [field for field in expected_fields if field in workflow_execution]
        
        assert len(present_fields) > 0, f"Workflow execution should contain at least one of these fields: {expected_fields}"
        print(f"Workflow execution contains these fields: {', '.join(present_fields)}")
        
        if "status" in workflow_execution:
            valid_statuses = ["running", "completed", "failed", "pending"]
            assert workflow_execution["status"] in valid_statuses, f"Execution status should be valid"
        
        if "execution_id" in workflow_execution:
            exec_id = workflow_execution["execution_id"]
            assert isinstance(exec_id, (str, int)), "Execution ID should be string or integer"
        
        print(f"Workflow execution structure: {workflow_execution}")
        
    elif isinstance(workflow_execution, str):
        success_indicators = ["success", "started", "running", "completed"]
        execution_lower = workflow_execution.lower()
        has_success_indicator = any(indicator in execution_lower for indicator in success_indicators)
        
        if has_success_indicator:
            print(f"Workflow execution appears successful: {workflow_execution}")
        else:
            print(f"Workflow execution response: {workflow_execution}")
    else:
        assert str(workflow_execution).strip() != "", "Workflow execution should not be empty"

    print(f"Successfully executed workflow")

    return True