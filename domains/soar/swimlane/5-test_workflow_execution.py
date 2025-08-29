# 5-test_workflow_execution.py

async def test_workflow_execution(zerg_state=None):
    """Test Swimlane SOAR workflow execution"""
    print("Testing Swimlane SOAR workflow execution")

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

    assert isinstance(app_selector.values, list), "app_selector values must be a list"
    application_id = app_selector.values[0] if app_selector.values else None
    print(f"Selecting application ID: {application_id}")

    assert application_id, f"failed to retrieve application ID from application selector"

    target = SwimlaneSOARTarget(application_ids=[application_id])
    assert isinstance(target, ConnectorTargetInterface), "SwimlaneSOARTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    create_record_tool = next(tool for tool in tools if tool.name == "create_record")
    
    test_record_data = {
        "title": "Test Security Incident",
        "description": "Test incident created by connector",
        "severity": "Medium",
        "source": "connector_test"
    }
    
    record_result = await create_record_tool.execute(
        application_id=application_id,
        record_data=test_record_data
    )
    record_creation = record_result.result

    print("Type of returned record_creation:", type(record_creation))
    print(f"Record creation preview: {str(record_creation)[:200]}")

    assert record_creation is not None, "record_creation should not be None"
    
    if isinstance(record_creation, dict):
        expected_fields = ["id", "trackingId", "applicationId", "createdDate", "values"]
        present_fields = [field for field in expected_fields if field in record_creation]
        
        assert len(present_fields) > 0, f"Record creation should contain at least one of these fields: {expected_fields}"
        print(f"Record creation contains these fields: {', '.join(present_fields)}")
        
        if "id" in record_creation:
            record_id = record_creation["id"]
            assert isinstance(record_id, str), "Record ID should be a string"
        
        if "trackingId" in record_creation:
            tracking_id = record_creation["trackingId"]
            assert isinstance(tracking_id, str), "Tracking ID should be a string"
        
        if "applicationId" in record_creation:
            app_id = record_creation["applicationId"]
            assert app_id == application_id, "Application ID should match target"
        
        print(f"Record creation structure: {record_creation}")
        
    elif isinstance(record_creation, str):
        success_indicators = ["success", "created", "saved"]
        creation_lower = record_creation.lower()
        has_success_indicator = any(indicator in creation_lower for indicator in success_indicators)
        
        if has_success_indicator:
            print(f"Record creation appears successful: {record_creation}")
        else:
            print(f"Record creation response: {record_creation}")
    else:
        assert str(record_creation).strip() != "", "Record creation should not be empty"

    print(f"Successfully created record")

    return True