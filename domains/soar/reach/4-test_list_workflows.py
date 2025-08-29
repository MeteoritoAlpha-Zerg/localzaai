# 4-test_list_workflows.py

async def test_list_workflows(zerg_state=None):
    """Test Reach SOAR workflow enumeration by way of connector tools"""
    print("Testing Reach SOAR workflow listing")

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

    num_workflows = 2
    assert isinstance(workflow_selector.values, list), "workflow_selector values must be a list"
    workflow_ids = workflow_selector.values[:num_workflows] if workflow_selector.values else None
    print(f"Selecting workflow IDs: {workflow_ids}")

    assert workflow_ids, f"failed to retrieve {num_workflows} workflow IDs from workflow selector"

    target = ReachSOARTarget(workflow_ids=workflow_ids)
    assert isinstance(target, ConnectorTargetInterface), "ReachSOARTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    reach_get_workflows_tool = next(tool for tool in tools if tool.name == "get_reach_workflows")
    reach_workflows_result = await reach_get_workflows_tool.execute()
    reach_workflows = reach_workflows_result.result

    print("Type of returned reach_workflows:", type(reach_workflows))
    print(f"len workflows: {len(reach_workflows)} workflows: {str(reach_workflows)[:200]}")

    assert isinstance(reach_workflows, list), "reach_workflows should be a list"
    assert len(reach_workflows) > 0, "reach_workflows should not be empty"
    assert len(reach_workflows) == num_workflows, f"reach_workflows should have {num_workflows} entries"
    
    for workflow in reach_workflows:
        assert "id" in workflow, "Each workflow should have an 'id' field"
        assert workflow["id"] in workflow_ids, f"Workflow ID {workflow['id']} is not in the requested workflow_ids"
        assert "name" in workflow, "Each workflow should have a 'name' field"
        assert "status" in workflow, "Each workflow should have a 'status' field"
        
        descriptive_fields = ["description", "category", "created_date", "last_modified", "trigger_type"]
        present_fields = [field for field in descriptive_fields if field in workflow]
        
        print(f"Workflow {workflow['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        if "status" in workflow:
            valid_statuses = ["active", "inactive", "draft"]
            assert workflow["status"] in valid_statuses, f"Workflow status should be valid"
        
        if workflow == reach_workflows[0]:
            print(f"Example workflow structure: {workflow}")

    print(f"Successfully retrieved and validated {len(reach_workflows)} Reach SOAR workflows")

    return True