# 6-test_get_actions.py

async def test_get_actions(zerg_state=None):
    """Test Splunk Phantom action results and event data retrieval"""
    print("Testing Splunk Phantom action results and event data retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    splunk_phantom_api_url = zerg_state.get("splunk_phantom_api_url").get("value")
    splunk_phantom_api_token = zerg_state.get("splunk_phantom_api_token").get("value")

    from connectors.splunk_phantom.config import SplunkPhantomConnectorConfig
    from connectors.splunk_phantom.connector import SplunkPhantomConnector
    from connectors.splunk_phantom.target import SplunkPhantomTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = SplunkPhantomConnectorConfig(
        api_url=splunk_phantom_api_url,
        api_token=splunk_phantom_api_token
    )
    assert isinstance(config, ConnectorConfig), "SplunkPhantomConnectorConfig should be of type ConnectorConfig"

    connector = SplunkPhantomConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SplunkPhantomConnector should be of type Connector"

    splunk_phantom_query_target_options = await connector.get_query_target_options()
    assert isinstance(splunk_phantom_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in splunk_phantom_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    actions_source = None
    for source in data_source_selector.values:
        if 'action' in source.lower():
            actions_source = source
            break
    
    assert actions_source, "Actions data source not found in available options"
    print(f"Selecting actions data source: {actions_source}")

    target = SplunkPhantomTarget(data_sources=[actions_source])
    assert isinstance(target, ConnectorTargetInterface), "SplunkPhantomTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_splunk_phantom_actions_tool = next(tool for tool in tools if tool.name == "get_splunk_phantom_actions")
    actions_result = await get_splunk_phantom_actions_tool.execute()
    actions_data = actions_result.result

    print("Type of returned actions data:", type(actions_data))
    print(f"Actions count: {len(actions_data)} sample: {str(actions_data)[:200]}")

    assert isinstance(actions_data, list), "Actions data should be a list"
    assert len(actions_data) > 0, "Actions data should not be empty"
    
    actions_to_check = actions_data[:10] if len(actions_data) > 10 else actions_data
    
    for action in actions_to_check:
        # Verify essential action fields per Splunk Phantom API specification
        assert "id" in action, "Each action should have an 'id' field"
        assert "action" in action, "Each action should have an 'action' field"
        assert "status" in action, "Each action should have a 'status' field"
        assert "create_time" in action, "Each action should have a 'create_time' field"
        
        assert action["id"], "Action ID should not be empty"
        assert action["action"].strip(), "Action name should not be empty"
        assert action["status"], "Action status should not be empty"
        
        # Verify action status is valid
        valid_statuses = ["success", "failed", "running", "pending"]
        status = action["status"].lower()
        assert any(valid_status in status for valid_status in valid_statuses), f"Invalid action status: {status}"
        
        action_fields = ["app", "playbook", "container", "message", "result_data", "summary"]
        present_fields = [field for field in action_fields if field in action]
        
        print(f"Action {action['id']} ({action['action']}, {action['status']}) contains: {', '.join(present_fields)}")
        
        # If app is present, validate it's not empty
        if "app" in action:
            app = action["app"]
            assert app and app.strip(), "App should not be empty"
        
        # If playbook is present, validate it's not empty
        if "playbook" in action:
            playbook = action["playbook"]
            assert playbook, "Playbook should not be empty"
        
        # If container is present, validate it's not empty
        if "container" in action:
            container = action["container"]
            assert container, "Container should not be empty"
        
        # If result data is present, validate structure
        if "result_data" in action:
            result_data = action["result_data"]
            assert isinstance(result_data, list), "Result data should be a list"
        
        # If summary is present, validate structure
        if "summary" in action:
            summary = action["summary"]
            assert isinstance(summary, dict), "Summary should be a dictionary"
        
        # Log the structure of the first action for debugging
        if action == actions_to_check[0]:
            print(f"Example action structure: {action}")

    print(f"Successfully retrieved and validated {len(actions_data)} Splunk Phantom actions")

    return True