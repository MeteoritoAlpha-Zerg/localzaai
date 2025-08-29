# 4-test_get_incidents.py

async def test_get_incidents(zerg_state=None):
    """Test Cortex XSIAM security incidents retrieval"""
    print("Testing Cortex XSIAM security incidents retrieval")

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

    # select incidents data source
    data_source_selector = None
    for selector in cortex_xsiam_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find incidents in available data sources
    incidents_source = None
    for source in data_source_selector.values:
        if 'incident' in source.lower():
            incidents_source = source
            break
    
    assert incidents_source, "Incidents data source not found in available options"
    print(f"Selecting incidents data source: {incidents_source}")

    # set up the target with incidents data source
    target = CortexXSIAMTarget(data_sources=[incidents_source])
    assert isinstance(target, ConnectorTargetInterface), "CortexXSIAMTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_cortex_xsiam_incidents tool
    cortex_xsiam_get_incidents_tool = next(tool for tool in tools if tool.name == "get_cortex_xsiam_incidents")
    incidents_result = await cortex_xsiam_get_incidents_tool.execute()
    incidents_data = incidents_result.result

    print("Type of returned incidents data:", type(incidents_data))
    print(f"Incidents count: {len(incidents_data)} sample: {str(incidents_data)[:200]}")

    # Verify that incidents_data is a list
    assert isinstance(incidents_data, list), "Incidents data should be a list"
    assert len(incidents_data) > 0, "Incidents data should not be empty"
    
    # Limit the number of incidents to check if there are many
    incidents_to_check = incidents_data[:5] if len(incidents_data) > 5 else incidents_data
    
    # Verify structure of each incident entry
    for incident in incidents_to_check:
        # Verify essential incident fields
        assert "incident_id" in incident, "Each incident should have an 'incident_id' field"
        assert "name" in incident, "Each incident should have a 'name' field"
        assert "status" in incident, "Each incident should have a 'status' field"
        assert "severity" in incident, "Each incident should have a 'severity' field"
        assert "created_time" in incident, "Each incident should have a 'created_time' field"
        
        # Verify incident status is valid
        valid_statuses = ["active", "pending", "resolved", "closed"]
        status = incident["status"].lower()
        assert any(valid_status in status for valid_status in valid_statuses), f"Invalid incident status: {status}"
        
        # Verify severity is valid
        valid_severities = ["low", "medium", "high", "critical"]
        severity = incident["severity"].lower()
        assert severity in valid_severities, f"Invalid severity level: {severity}"
        
        # Check for additional incident fields
        incident_fields = ["description", "alert_count", "assigned_user", "last_modified", "playbook_id", "investigation_id"]
        present_fields = [field for field in incident_fields if field in incident]
        
        print(f"Incident {incident['incident_id']} ({incident['severity']}, {incident['status']}) contains: {', '.join(present_fields)}")
        
        # Verify incident ID and name are not empty
        assert incident["incident_id"], "Incident ID should not be empty"
        assert incident["name"].strip(), "Incident name should not be empty"
        
        # If alert count is present, verify it's numeric
        if "alert_count" in incident:
            alert_count = incident["alert_count"]
            assert isinstance(alert_count, int), "Alert count should be an integer"
            assert alert_count >= 0, "Alert count should be non-negative"
        
        # If assigned user is present, validate it's not empty
        if "assigned_user" in incident:
            assigned_user = incident["assigned_user"]
            assert assigned_user and assigned_user.strip(), "Assigned user should not be empty"
        
        # If playbook ID is present, validate it's not empty
        if "playbook_id" in incident:
            playbook_id = incident["playbook_id"]
            assert playbook_id, "Playbook ID should not be empty"
        
        # If investigation ID is present, validate it's not empty
        if "investigation_id" in incident:
            investigation_id = incident["investigation_id"]
            assert investigation_id, "Investigation ID should not be empty"
        
        # Log the structure of the first incident for debugging
        if incident == incidents_to_check[0]:
            print(f"Example incident structure: {incident}")

    print(f"Successfully retrieved and validated {len(incidents_data)} Cortex XSIAM incidents")

    return True