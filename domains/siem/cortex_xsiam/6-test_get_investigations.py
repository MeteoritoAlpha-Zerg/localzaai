# 6-test_get_investigations.py

async def test_get_investigations(zerg_state=None):
    """Test Cortex XSIAM investigation and automation data retrieval"""
    print("Testing Cortex XSIAM investigation and automation data retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    cortex_xsiam_api_url = zerg_state.get("cortex_xsiam_api_url").get("value")
    cortex_xsiam_api_key = zerg_state.get("cortex_xsiam_api_key").get("value")
    cortex_xsiam_api_key_id = zerg_state.get("cortex_xsiam_api_key_id").get("value")
    cortex_xsiam_tenant_id = zerg_state.get("cortex_xsiam_tenant_id").get("value")

    from connectors.cortex_xsiam.config import CortexXSIAMConnectorConfig
    from connectors.cortex_xsiam.connector import CortexXSIAMConnector
    from connectors.cortex_xsiam.target import CortexXSIAMTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = CortexXSIAMConnectorConfig(
        api_url=cortex_xsiam_api_url,
        api_key=cortex_xsiam_api_key,
        api_key_id=cortex_xsiam_api_key_id,
        tenant_id=cortex_xsiam_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "CortexXSIAMConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CortexXSIAMConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CortexXSIAMConnector should be of type Connector"

    # get query target options
    cortex_xsiam_query_target_options = await connector.get_query_target_options()
    assert isinstance(cortex_xsiam_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select investigations data source
    data_source_selector = None
    for selector in cortex_xsiam_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find investigations in available data sources
    investigations_source = None
    for source in data_source_selector.values:
        if 'investigation' in source.lower() or 'playbook' in source.lower():
            investigations_source = source
            break
    
    assert investigations_source, "Investigations data source not found in available options"
    print(f"Selecting investigations data source: {investigations_source}")

    # set up the target with investigations data source
    target = CortexXSIAMTarget(data_sources=[investigations_source])
    assert isinstance(target, ConnectorTargetInterface), "CortexXSIAMTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_cortex_xsiam_investigations tool and execute it
    get_cortex_xsiam_investigations_tool = next(tool for tool in tools if tool.name == "get_cortex_xsiam_investigations")
    investigations_result = await get_cortex_xsiam_investigations_tool.execute()
    investigations_data = investigations_result.result

    print("Type of returned investigations data:", type(investigations_data))
    print(f"Investigations count: {len(investigations_data)} sample: {str(investigations_data)[:200]}")

    # Verify that investigations_data is a list
    assert isinstance(investigations_data, list), "Investigations data should be a list"
    assert len(investigations_data) > 0, "Investigations data should not be empty"
    
    # Limit the number of investigations to check if there are many
    investigations_to_check = investigations_data[:5] if len(investigations_data) > 5 else investigations_data
    
    # Verify structure of each investigation entry
    for investigation in investigations_to_check:
        # Verify essential investigation fields
        assert "id" in investigation, "Each investigation should have an 'id' field"
        assert "name" in investigation, "Each investigation should have a 'name' field"
        assert "status" in investigation, "Each investigation should have a 'status' field"
        assert "created_time" in investigation, "Each investigation should have a 'created_time' field"
        
        # Verify investigation status is valid
        valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        status = investigation["status"].lower()
        assert any(valid_status in status for valid_status in valid_statuses), f"Invalid investigation status: {status}"
        
        # Verify investigation ID and name are not empty
        assert investigation["id"], "Investigation ID should not be empty"
        assert investigation["name"].strip(), "Investigation name should not be empty"
        
        # Check for additional investigation fields
        investigation_fields = ["type", "incident_id", "playbook_id", "owner", "start_time", "end_time", "tasks", "outputs"]
        present_fields = [field for field in investigation_fields if field in investigation]
        
        print(f"Investigation {investigation['id']} ({investigation['name']}, {investigation['status']}) contains: {', '.join(present_fields)}")
        
        # If type is present, validate it's not empty
        if "type" in investigation:
            inv_type = investigation["type"]
            assert inv_type and inv_type.strip(), "Investigation type should not be empty"
        
        # If incident ID is present, validate it's not empty
        if "incident_id" in investigation:
            incident_id = investigation["incident_id"]
            assert incident_id, "Incident ID should not be empty"
        
        # If playbook ID is present, validate it's not empty
        if "playbook_id" in investigation:
            playbook_id = investigation["playbook_id"]
            assert playbook_id, "Playbook ID should not be empty"
        
        # If owner is present, validate it's not empty
        if "owner" in investigation:
            owner = investigation["owner"]
            assert owner and owner.strip(), "Investigation owner should not be empty"
        
        # If tasks are present, validate structure
        if "tasks" in investigation:
            tasks = investigation["tasks"]
            assert isinstance(tasks, list), "Tasks should be a list"
            for task in tasks:
                assert isinstance(task, dict), "Each task should be a dictionary"
                assert "id" in task, "Each task should have an id"
                assert "name" in task, "Each task should have a name"
        
        # If outputs are present, validate structure
        if "outputs" in investigation:
            outputs = investigation["outputs"]
            assert isinstance(outputs, dict), "Outputs should be a dictionary"
        
        # Log the structure of the first investigation for debugging
        if investigation == investigations_to_check[0]:
            print(f"Example investigation structure: {investigation}")

    print(f"Successfully retrieved and validated {len(investigations_data)} Cortex XSIAM investigations")

    return True