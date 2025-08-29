# 5-test_get_playbooks.py

async def test_get_playbooks(zerg_state=None):
    """Test Splunk Phantom playbooks and automation workflows retrieval"""
    print("Testing Splunk Phantom playbooks and automation workflows retrieval")

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
    
    playbooks_source = None
    for source in data_source_selector.values:
        if 'playbook' in source.lower():
            playbooks_source = source
            break
    
    assert playbooks_source, "Playbooks data source not found in available options"
    print(f"Selecting playbooks data source: {playbooks_source}")

    target = SplunkPhantomTarget(data_sources=[playbooks_source])
    assert isinstance(target, ConnectorTargetInterface), "SplunkPhantomTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_splunk_phantom_playbooks_tool = next(tool for tool in tools if tool.name == "get_splunk_phantom_playbooks")
    playbooks_result = await get_splunk_phantom_playbooks_tool.execute()
    playbooks_data = playbooks_result.result

    print("Type of returned playbooks data:", type(playbooks_data))
    print(f"Playbooks count: {len(playbooks_data)} sample: {str(playbooks_data)[:200]}")

    assert isinstance(playbooks_data, list), "Playbooks data should be a list"
    assert len(playbooks_data) > 0, "Playbooks data should not be empty"
    
    playbooks_to_check = playbooks_data[:5] if len(playbooks_data) > 5 else playbooks_data
    
    for playbook in playbooks_to_check:
        # Verify essential playbook fields per Splunk Phantom API specification
        assert "id" in playbook, "Each playbook should have an 'id' field"
        assert "name" in playbook, "Each playbook should have a 'name' field"
        assert "active" in playbook, "Each playbook should have an 'active' field"
        
        assert playbook["id"], "Playbook ID should not be empty"
        assert playbook["name"].strip(), "Playbook name should not be empty"
        assert isinstance(playbook["active"], bool), "Active field should be boolean"
        
        playbook_fields = ["description", "type", "tags", "create_time", "last_run_time", "run_count"]
        present_fields = [field for field in playbook_fields if field in playbook]
        
        print(f"Playbook {playbook['id']} ({playbook['name']}, active: {playbook['active']}) contains: {', '.join(present_fields)}")
        
        # If type is present, validate it's a valid playbook type
        if "type" in playbook:
            playbook_type = playbook["type"]
            valid_types = ["automation", "input", "data"]
            assert playbook_type.lower() in valid_types, f"Invalid playbook type: {playbook_type}"
        
        # If run count is present, verify it's numeric
        if "run_count" in playbook:
            run_count = playbook["run_count"]
            assert isinstance(run_count, int), "Run count should be an integer"
            assert run_count >= 0, "Run count should be non-negative"
        
        # If tags are present, validate structure
        if "tags" in playbook:
            tags = playbook["tags"]
            assert isinstance(tags, list), "Tags should be a list"
            for tag in tags:
                assert isinstance(tag, str), "Each tag should be a string"
                assert tag.strip(), "Tag should not be empty"
        
        # Log the structure of the first playbook for debugging
        if playbook == playbooks_to_check[0]:
            print(f"Example playbook structure: {playbook}")

    print(f"Successfully retrieved and validated {len(playbooks_data)} Splunk Phantom playbooks")

    return True