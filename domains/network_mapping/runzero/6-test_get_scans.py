# 6-test_get_scans.py

async def test_get_scans(zerg_state=None):
    """Test RunZero network scan results retrieval"""
    print("Testing RunZero network scan results retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    runzero_api_url = zerg_state.get("runzero_api_url").get("value")
    runzero_api_token = zerg_state.get("runzero_api_token").get("value")
    runzero_organization_id = zerg_state.get("runzero_organization_id").get("value")

    from connectors.runzero.config import RunZeroConnectorConfig
    from connectors.runzero.connector import RunZeroConnector
    from connectors.runzero.target import RunZeroTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = RunZeroConnectorConfig(
        api_url=runzero_api_url,
        api_token=runzero_api_token,
        organization_id=runzero_organization_id
    )
    assert isinstance(config, ConnectorConfig), "RunZeroConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = RunZeroConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RunZeroConnector should be of type Connector"

    # get query target options
    runzero_query_target_options = await connector.get_query_target_options()
    assert isinstance(runzero_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select scans data source
    data_source_selector = None
    for selector in runzero_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find scans in available data sources
    scans_source = None
    for source in data_source_selector.values:
        if 'scan' in source.lower():
            scans_source = source
            break
    
    assert scans_source, "Scans data source not found in available options"
    print(f"Selecting scans data source: {scans_source}")

    # set up the target with scans data source
    target = RunZeroTarget(data_sources=[scans_source])
    assert isinstance(target, ConnectorTargetInterface), "RunZeroTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_runzero_scans tool and execute it
    get_runzero_scans_tool = next(tool for tool in tools if tool.name == "get_runzero_scans")
    scans_result = await get_runzero_scans_tool.execute()
    scans_data = scans_result.result

    print("Type of returned scans data:", type(scans_data))
    print(f"Scans count: {len(scans_data)} sample: {str(scans_data)[:200]}")

    # Verify that scans_data is a list
    assert isinstance(scans_data, list), "Scans data should be a list"
    assert len(scans_data) > 0, "Scans data should not be empty"
    
    # Limit the number of scans to check if there are many
    scans_to_check = scans_data[:5] if len(scans_data) > 5 else scans_data
    
    # Verify structure of each scan entry
    for scan in scans_to_check:
        # Verify essential scan fields per RunZero API specification
        assert "id" in scan, "Each scan should have an 'id' field"
        assert "name" in scan, "Each scan should have a 'name' field"
        assert "status" in scan, "Each scan should have a 'status' field"
        assert "created_at" in scan, "Each scan should have a 'created_at' field"
        
        # Verify scan status is valid
        valid_statuses = ["completed", "running", "stopped", "failed", "pending", "queued"]
        status = scan["status"].lower()
        assert any(valid_status in status for valid_status in valid_statuses), f"Invalid scan status: {status}"
        
        # Verify scan name and ID are not empty
        assert scan["name"].strip(), "Scan name should not be empty"
        assert scan["id"], "Scan ID should not be empty"
        
        # Check for additional scan fields per RunZero specification
        scan_fields = ["started_at", "completed_at", "targets", "agent", "task_count", "assets_new", "assets_total", "services_new", "services_total"]
        present_fields = [field for field in scan_fields if field in scan]
        
        print(f"Scan {scan['id']} ({scan['name']}, {scan['status']}) contains: {', '.join(present_fields)}")
        
        # If targets are present, validate structure
        if "targets" in scan:
            targets = scan["targets"]
            if isinstance(targets, list):
                for target in targets:
                    assert isinstance(target, str), "Each target should be a string"
                    assert target.strip(), "Target should not be empty"
        
        # If task count is present, verify it's numeric
        if "task_count" in scan:
            task_count = scan["task_count"]
            assert isinstance(task_count, int), "Task count should be an integer"
            assert task_count >= 0, "Task count should be non-negative"
        
        # If asset counts are present, verify they're numeric
        if "assets_new" in scan:
            assets_new = scan["assets_new"]
            assert isinstance(assets_new, int), "New assets count should be an integer"
            assert assets_new >= 0, "New assets count should be non-negative"
        
        if "assets_total" in scan:
            assets_total = scan["assets_total"]
            assert isinstance(assets_total, int), "Total assets count should be an integer"
            assert assets_total >= 0, "Total assets count should be non-negative"
        
        # If service counts are present, verify they're numeric
        if "services_new" in scan:
            services_new = scan["services_new"]
            assert isinstance(services_new, int), "New services count should be an integer"
            assert services_new >= 0, "New services count should be non-negative"
        
        if "services_total" in scan:
            services_total = scan["services_total"]
            assert isinstance(services_total, int), "Total services count should be an integer"
            assert services_total >= 0, "Total services count should be non-negative"
        
        # If agent information is present, validate it's not empty
        if "agent" in scan:
            agent = scan["agent"]
            assert agent and agent.strip(), "Agent information should not be empty"
        
        # Log the structure of the first scan for debugging
        if scan == scans_to_check[0]:
            print(f"Example scan structure: {scan}")

    print(f"Successfully retrieved and validated {len(scans_data)} RunZero scans")

    return True