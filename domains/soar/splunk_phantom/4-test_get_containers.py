# 4-test_get_containers.py

async def test_get_containers(zerg_state=None):
    """Test Splunk Phantom security containers retrieval"""
    print("Testing Splunk Phantom security containers retrieval")

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
    
    containers_source = None
    for source in data_source_selector.values:
        if 'container' in source.lower():
            containers_source = source
            break
    
    assert containers_source, "Containers data source not found in available options"
    print(f"Selecting containers data source: {containers_source}")

    target = SplunkPhantomTarget(data_sources=[containers_source])
    assert isinstance(target, ConnectorTargetInterface), "SplunkPhantomTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    splunk_phantom_get_containers_tool = next(tool for tool in tools if tool.name == "get_splunk_phantom_containers")
    containers_result = await splunk_phantom_get_containers_tool.execute()
    containers_data = containers_result.result

    print("Type of returned containers data:", type(containers_data))
    print(f"Containers count: {len(containers_data)} sample: {str(containers_data)[:200]}")

    assert isinstance(containers_data, list), "Containers data should be a list"
    assert len(containers_data) > 0, "Containers data should not be empty"
    
    containers_to_check = containers_data[:5] if len(containers_data) > 5 else containers_data
    
    for container in containers_to_check:
        # Verify essential container fields per Splunk Phantom API specification
        assert "id" in container, "Each container should have an 'id' field"
        assert "name" in container, "Each container should have a 'name' field"
        assert "status" in container, "Each container should have a 'status' field"
        assert "severity" in container, "Each container should have a 'severity' field"
        assert "create_time" in container, "Each container should have a 'create_time' field"
        
        # Verify container status is valid
        valid_statuses = ["new", "open", "closed"]
        status = container["status"].lower()
        assert status in valid_statuses, f"Invalid container status: {status}"
        
        # Verify severity is valid
        valid_severities = ["low", "medium", "high"]
        severity = container["severity"].lower()
        assert severity in valid_severities, f"Invalid severity level: {severity}"
        
        container_fields = ["label", "description", "owner", "source_data_identifier", "artifact_count", "tags"]
        present_fields = [field for field in container_fields if field in container]
        
        print(f"Container {container['id']} ({container['severity']}, {container['status']}) contains: {', '.join(present_fields)}")
        
        assert container["id"], "Container ID should not be empty"
        assert container["name"].strip(), "Container name should not be empty"
        
        # If artifact count is present, verify it's numeric
        if "artifact_count" in container:
            artifact_count = container["artifact_count"]
            assert isinstance(artifact_count, int), "Artifact count should be an integer"
            assert artifact_count >= 0, "Artifact count should be non-negative"
        
        # If tags are present, validate structure
        if "tags" in container:
            tags = container["tags"]
            assert isinstance(tags, list), "Tags should be a list"
            for tag in tags:
                assert isinstance(tag, str), "Each tag should be a string"
                assert tag.strip(), "Tag should not be empty"
        
        # Log the structure of the first container for debugging
        if container == containers_to_check[0]:
            print(f"Example container structure: {container}")

    print(f"Successfully retrieved and validated {len(containers_data)} Splunk Phantom containers")

    return True