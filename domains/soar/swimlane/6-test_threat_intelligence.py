# 6-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Swimlane SOAR threat intelligence processing"""
    print("Testing Swimlane SOAR threat intelligence processing")

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
    print(f"Using application for threat intelligence processing: {application_id}")

    assert application_id, f"failed to retrieve application ID from application selector"

    target = SwimlaneSOARTarget(application_ids=[application_id])
    assert isinstance(target, ConnectorTargetInterface), "SwimlaneSOARTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    process_threat_intel_tool = next(tool for tool in tools if tool.name == "process_threat_intelligence")
    
    test_threat_data = {
        "ioc_type": "ip_address",
        "ioc_value": "192.168.1.100",
        "threat_type": "malware",
        "confidence": "high",
        "source": "connector_test"
    }
    
    threat_intel_result = await process_threat_intel_tool.execute(
        application_id=application_id,
        threat_data=test_threat_data
    )
    threat_intelligence = threat_intel_result.result

    print("Type of returned threat_intelligence:", type(threat_intelligence))
    print(f"Threat intelligence preview: {str(threat_intelligence)[:200]}")

    assert threat_intelligence is not None, "threat_intelligence should not be None"
    
    if isinstance(threat_intelligence, dict):
        expected_fields = ["record_id", "ioc_analysis", "enrichment_data", "automated_actions", "risk_assessment"]
        present_fields = [field for field in expected_fields if field in threat_intelligence]
        
        if len(present_fields) > 0:
            print(f"Threat intelligence contains these fields: {', '.join(present_fields)}")
            
            if "record_id" in threat_intelligence:
                record_id = threat_intelligence["record_id"]
                assert isinstance(record_id, str), "Record ID should be a string"
            
            if "ioc_analysis" in threat_intelligence:
                ioc_analysis = threat_intelligence["ioc_analysis"]
                assert isinstance(ioc_analysis, dict), "IOC analysis should be a dictionary"
            
            if "risk_assessment" in threat_intelligence:
                risk_assessment = threat_intelligence["risk_assessment"]
                if isinstance(risk_assessment, dict) and "score" in risk_assessment:
                    score = risk_assessment["score"]
                    assert isinstance(score, (int, float)), "Risk score should be numeric"
        
        print(f"Threat intelligence structure: {threat_intelligence}")
        
    elif isinstance(threat_intelligence, list):
        assert len(threat_intelligence) > 0, "Threat intelligence list should not be empty"
        
        sample_item = threat_intelligence[0]
        assert isinstance(sample_item, dict), "Threat intelligence items should be dictionaries"
        
        item_fields = ["ioc", "enrichment", "analysis", "actions"]
        present_item_fields = [field for field in item_fields if field in sample_item]
        
        print(f"Threat intelligence items contain these fields: {', '.join(present_item_fields)}")
        print(f"Example threat intelligence item: {sample_item}")
        
    else:
        assert str(threat_intelligence).strip() != "", "Threat intelligence should contain meaningful data"

    print(f"Successfully processed threat intelligence data")

    return True