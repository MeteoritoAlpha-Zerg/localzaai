# 5-test_get_incidents.py

async def test_get_incidents(zerg_state=None):
    """Test RSA Archer incident management data retrieval"""
    print("Testing RSA Archer incident management data retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    rsa_archer_api_url = zerg_state.get("rsa_archer_api_url").get("value")
    rsa_archer_username = zerg_state.get("rsa_archer_username").get("value")
    rsa_archer_password = zerg_state.get("rsa_archer_password").get("value")
    rsa_archer_instance_name = zerg_state.get("rsa_archer_instance_name").get("value")

    from connectors.rsa_archer.config import RSAArcherConnectorConfig
    from connectors.rsa_archer.connector import RSAArcherConnector
    from connectors.rsa_archer.target import RSAArcherTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = RSAArcherConnectorConfig(
        api_url=rsa_archer_api_url,
        username=rsa_archer_username,
        password=rsa_archer_password,
        instance_name=rsa_archer_instance_name
    )
    assert isinstance(config, ConnectorConfig), "RSAArcherConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = RSAArcherConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RSAArcherConnector should be of type Connector"

    # get query target options
    rsa_archer_query_target_options = await connector.get_query_target_options()
    assert isinstance(rsa_archer_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select incident-related application
    application_selector = None
    for selector in rsa_archer_query_target_options.selectors:
        if selector.type == 'applications':  
            application_selector = selector
            break

    assert application_selector, "failed to retrieve application selector from query target options"
    assert isinstance(application_selector.values, list), "application_selector values must be a list"
    
    # Find incident-related application
    incident_application = None
    for app in application_selector.values:
        if 'incident' in app.lower() or 'security' in app.lower():
            incident_application = app
            break
    
    # If no incident-specific app found, use the first available application
    if not incident_application:
        incident_application = application_selector.values[0]
    
    assert incident_application, "No applications available for incident retrieval"
    print(f"Selecting incident application: {incident_application}")

    # set up the target with incident application
    target = RSAArcherTarget(applications=[incident_application])
    assert isinstance(target, ConnectorTargetInterface), "RSAArcherTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_rsa_archer_incidents tool and execute it
    get_rsa_archer_incidents_tool = next(tool for tool in tools if tool.name == "get_rsa_archer_incidents")
    incidents_result = await get_rsa_archer_incidents_tool.execute(application=incident_application)
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
        # Verify essential incident fields per RSA Archer API specification
        assert "Id" in incident or "id" in incident, "Each incident should have an 'Id' or 'id' field"
        
        # Get the incident ID
        incident_id = incident.get("Id") or incident.get("id")
        assert incident_id, "Incident ID should not be empty"
        
        # Check for additional incident fields per RSA Archer specification
        incident_fields = ["Title", "Status", "Severity", "Priority", "Description", "CreatedDate", "ModifiedDate", "AssignedTo", "Fields"]
        present_fields = [field for field in incident_fields if field in incident]
        
        print(f"Incident {incident_id} contains: {', '.join(present_fields)}")
        
        # If Status is present, validate it's not empty
        if "Status" in incident:
            status = incident["Status"]
            assert status, "Incident status should not be empty"
        
        # If Severity is present, validate it's not empty
        if "Severity" in incident:
            severity = incident["Severity"]
            assert severity, "Incident severity should not be empty"
        
        # If Priority is present, validate it's not empty
        if "Priority" in incident:
            priority = incident["Priority"]
            assert priority, "Incident priority should not be empty"
        
        # If Title is present, validate it's not empty
        if "Title" in incident:
            title = incident["Title"]
            assert title and title.strip(), "Incident title should not be empty"
        
        # If Description is present, validate it's not empty
        if "Description" in incident:
            description = incident["Description"]
            assert description and description.strip(), "Incident description should not be empty"
        
        # If Fields are present, validate structure
        if "Fields" in incident:
            fields = incident["Fields"]
            assert isinstance(fields, (dict, list)), "Fields should be a dictionary or list"
        
        # If AssignedTo is present, validate it's not empty
        if "AssignedTo" in incident:
            assigned_to = incident["AssignedTo"]
            assert assigned_to, "AssignedTo should not be empty"
        
        # Log the structure of the first incident for debugging
        if incident == incidents_to_check[0]:
            print(f"Example incident structure: {incident}")

    print(f"Successfully retrieved and validated {len(incidents_data)} RSA Archer incidents")

    return True