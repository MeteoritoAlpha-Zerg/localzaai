# 5-test_playbook_execution.py

async def test_playbook_execution(zerg_state=None):
    """Test Revelstoke SOAR playbook execution and incident management"""
    print("Attempting to execute playbooks using Revelstoke SOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    revelstoke_url = zerg_state.get("revelstoke_url").get("value")
    revelstoke_api_key = zerg_state.get("revelstoke_api_key", {}).get("value")
    revelstoke_username = zerg_state.get("revelstoke_username", {}).get("value")
    revelstoke_password = zerg_state.get("revelstoke_password", {}).get("value")
    revelstoke_tenant_id = zerg_state.get("revelstoke_tenant_id", {}).get("value")

    from connectors.revelstoke.config import RevelstokeSoarConnectorConfig
    from connectors.revelstoke.connector import RevelstokeSoarConnector
    from connectors.revelstoke.tools import RevelstokeSoarConnectorTools
    from connectors.revelstoke.target import RevelstokeSoarTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # prefer API key over username/password
    if revelstoke_api_key:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            api_key=revelstoke_api_key,
            tenant_id=revelstoke_tenant_id,
        )
    elif revelstoke_username and revelstoke_password:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            username=revelstoke_username,
            password=revelstoke_password,
            tenant_id=revelstoke_tenant_id,
        )
    else:
        raise Exception("Either revelstoke_api_key or both revelstoke_username and revelstoke_password must be provided")

    assert isinstance(config, ConnectorConfig), "RevelstokeSoarConnectorConfig should be of type ConnectorConfig"

    connector = RevelstokeSoarConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RevelstokeSoarConnector should be of type Connector"

    revelstoke_query_target_options = await connector.get_query_target_options()
    assert isinstance(revelstoke_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    playbook_selector = None
    for selector in revelstoke_query_target_options.selectors:
        if selector.type == 'playbook_ids':  
            playbook_selector = selector
            break

    assert playbook_selector, "failed to retrieve playbook selector from query target options"

    assert isinstance(playbook_selector.values, list), "playbook_selector values must be a list"
    playbook_id = playbook_selector.values[0] if playbook_selector.values else None
    print(f"Selecting playbook ID: {playbook_id}")

    assert playbook_id, f"failed to retrieve playbook ID from playbook selector"

    target = RevelstokeSoarTarget(playbook_ids=[playbook_id])
    assert isinstance(target, ConnectorTargetInterface), "RevelstokeSoarTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Execute playbook
    execute_revelstoke_playbook_tool = next(tool for tool in tools if tool.name == "execute_revelstoke_playbook")
    
    test_input_data = {
        "source_ip": "192.168.1.100",
        "alert_severity": "high",
        "alert_type": "malware_detection"
    }
    
    revelstoke_execution_result = await execute_revelstoke_playbook_tool.execute(
        playbook_id=playbook_id,
        input_data=test_input_data,
        timeout=300
    )
    revelstoke_execution = revelstoke_execution_result.result

    print("Type of returned revelstoke_execution:", type(revelstoke_execution))
    print(f"Execution result: {str(revelstoke_execution)[:200]}")

    assert isinstance(revelstoke_execution, dict), "revelstoke_execution should be a dictionary"
    assert "execution_id" in revelstoke_execution, "Execution result should have an 'execution_id' field"
    assert "status" in revelstoke_execution, "Execution result should have a 'status' field"
    
    valid_statuses = ["running", "completed", "failed", "pending"]
    assert revelstoke_execution["status"] in valid_statuses, f"Execution status {revelstoke_execution['status']} is not valid"
    
    execution_fields = ["playbook_id", "started_at", "completed_at", "steps", "outputs"]
    present_execution_fields = [field for field in execution_fields if field in revelstoke_execution]
    
    print(f"Execution result contains these fields: {', '.join(present_execution_fields)}")

    print(f"Successfully executed Revelstoke SOAR playbook {playbook_id}")

    # Test 2: Get cases/incidents
    get_revelstoke_cases_tool = next(tool for tool in tools if tool.name == "get_revelstoke_cases")
    revelstoke_cases_result = await get_revelstoke_cases_tool.execute(limit=10)
    revelstoke_cases = revelstoke_cases_result.result

    print("Type of returned revelstoke_cases:", type(revelstoke_cases))

    assert isinstance(revelstoke_cases, list), "revelstoke_cases should be a list"
    
    if len(revelstoke_cases) > 0:
        cases_to_check = revelstoke_cases[:3] if len(revelstoke_cases) > 3 else revelstoke_cases
        
        for case in cases_to_check:
            assert "id" in case, "Each case should have an 'id' field"
            assert "title" in case, "Each case should have a 'title' field"
            assert "status" in case, "Each case should have a 'status' field"
            assert "severity" in case, "Each case should have a 'severity' field"
            
            valid_case_statuses = ["new", "assigned", "in_progress", "resolved", "closed"]
            assert case["status"] in valid_case_statuses, f"Case status {case['status']} is not valid"
            
            print(f"Case {case['id']}: {case['title']} - {case['status']}")

        print(f"Successfully retrieved and validated {len(revelstoke_cases)} Revelstoke SOAR cases")

    # Test 3: Get workflow executions
    get_revelstoke_executions_tool = next(tool for tool in tools if tool.name == "get_revelstoke_executions")
    revelstoke_executions_result = await get_revelstoke_executions_tool.execute(limit=5)
    revelstoke_executions = revelstoke_executions_result.result

    print("Type of returned revelstoke_executions:", type(revelstoke_executions))

    assert isinstance(revelstoke_executions, list), "revelstoke_executions should be a list"
    
    if len(revelstoke_executions) > 0:
        executions_to_check = revelstoke_executions[:3] if len(revelstoke_executions) > 3 else revelstoke_executions
        
        for execution in executions_to_check:
            assert "id" in execution, "Each execution should have an 'id' field"
            assert "playbook_id" in execution, "Each execution should have a 'playbook_id' field"
            assert "status" in execution, "Each execution should have a 'status' field"
            
            print(f"Execution {execution['id']} for playbook {execution['playbook_id']}: {execution['status']}")

        print(f"Successfully retrieved and validated {len(revelstoke_executions)} Revelstoke SOAR executions")

    print("Successfully completed playbook execution and incident management tests")

    return True