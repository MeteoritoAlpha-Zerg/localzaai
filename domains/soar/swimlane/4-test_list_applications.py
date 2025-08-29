# 4-test_list_applications.py

async def test_list_applications(zerg_state=None):
    """Test Swimlane SOAR application enumeration by way of connector tools"""
    print("Testing Swimlane SOAR application listing")

    assert zerg_state, "this test requires valid zerg_state"

    swimlane_host = zerg_state.get("swimlane_host").get("value")
    swimlane_api_token = zerg_state.get("swimlane_api_token").get("value")
    swimlane_user_id = zerg_state.get("swimlane_user_id").get("value")

    from connectors.swimlane_soar.config import SwimlaneSOARConnectorConfig
    from connectors.swimlane_soar.connector import SwimlaneSOARConnector
    from connectors.swimlane_soar.target import SwimlaneSOARTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = SwimlaneSOARConnectorConfig(
        host=swimlane_host,
        api_token=swimlane_api_token,
        user_id=swimlane_user_id
    )
    assert isinstance(config, ConnectorConfig), "SwimlaneSOARConnectorConfig should be of type ConnectorConfig"

    connector = SwimlaneSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SwimlaneSOARConnector should be of type Connector"

    swimlane_query_target_options = await connector.get_query_target_options()
    assert isinstance(swimlane_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    app_selector = None
    for selector in swimlane_query_target_options.selectors:
        if selector.type == 'application_ids':  
            app_selector = selector
            break

    assert app_selector, "failed to retrieve application selector from query target options"

    num_applications = 2
    assert isinstance(app_selector.values, list), "app_selector values must be a list"
    application_ids = app_selector.values[:num_applications] if app_selector.values else None
    print(f"Selecting application IDs: {application_ids}")

    assert application_ids, f"failed to retrieve {num_applications} application IDs from application selector"

    target = SwimlaneSOARTarget(application_ids=application_ids)
    assert isinstance(target, ConnectorTargetInterface), "SwimlaneSOARTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    swimlane_get_applications_tool = next(tool for tool in tools if tool.name == "get_swimlane_applications")
    swimlane_applications_result = await swimlane_get_applications_tool.execute()
    swimlane_applications = swimlane_applications_result.result

    print("Type of returned swimlane_applications:", type(swimlane_applications))
    print(f"len applications: {len(swimlane_applications)} applications: {str(swimlane_applications)[:200]}")

    assert isinstance(swimlane_applications, list), "swimlane_applications should be a list"
    assert len(swimlane_applications) > 0, "swimlane_applications should not be empty"
    assert len(swimlane_applications) == num_applications, f"swimlane_applications should have {num_applications} entries"
    
    for application in swimlane_applications:
        assert "id" in application, "Each application should have an 'id' field"
        assert application["id"] in application_ids, f"Application ID {application['id']} is not in the requested application_ids"
        assert "name" in application, "Each application should have a 'name' field"
        assert "acronym" in application, "Each application should have an 'acronym' field"
        
        descriptive_fields = ["description", "trackingId", "workspaceId", "fields", "layout"]
        present_fields = [field for field in descriptive_fields if field in application]
        
        print(f"Application {application['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        if "trackingId" in application:
            tracking_id = application["trackingId"]
            assert isinstance(tracking_id, str), "Tracking ID should be a string"
        
        if "fields" in application:
            fields = application["fields"]
            assert isinstance(fields, list), "Fields should be a list"
        
        if application == swimlane_applications[0]:
            print(f"Example application structure: {application}")

    print(f"Successfully retrieved and validated {len(swimlane_applications)} Swimlane SOAR applications")

    return True