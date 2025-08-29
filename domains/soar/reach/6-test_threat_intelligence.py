# 6-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Reach SOAR threat intelligence processing"""
    print("Testing Reach SOAR threat intelligence processing")

    assert zerg_state, "this test requires valid zerg_state"

    reach_soar_api_token = zerg_state.get("reach_soar_api_token").get("value")
    reach_soar_base_url = zerg_state.get("reach_soar_base_url").get("value")
    reach_soar_tenant_id = zerg_state.get("reach_soar_tenant_id").get("value")

    from connectors.reach_soar.config import ReachSOARConnectorConfig
    from connectors.reach_soar.connector import ReachSOARConnector
    from connectors.reach_soar.target import ReachSOARTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = ReachSOARConnectorConfig(
        api_token=reach_soar_api_token,
        base_url=reach_soar_base_url,
        tenant_id=reach_soar_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "ReachSOARConnectorConfig should be of type ConnectorConfig"

    connector = ReachSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ReachSOARConnector should be of type Connector"

    reach_soar_query_target_options = await connector.get_query_target_options()
    assert isinstance(reach_soar_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    workflow_selector = None
    for selector in reach_soar_query_target_options.selectors:
        if selector.type == 'workflow_ids':  
            workflow_selector = selector
            break

    assert workflow_selector, "failed to retrieve workflow selector from query target options"

    assert isinstance(workflow_selector.values, list), "workflow_selector values must be a list"
    workflow_id = workflow_selector.values[0] if workflow_selector.values else None
    print(f"Using workflow for threat intelligence processing: {workflow_id}")

    assert workflow_id, f"failed to retrieve workflow ID from workflow selector"

    target = ReachSOARTarget(workflow_ids=[workflow_id])
    assert isinstance(target, ConnectorTargetInterface), "ReachSOARTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    process_threat_intel_tool = next(tool for tool in tools if tool.name == "process_threat_intelligence")
    
    test_threat_data = {
        "indicators": [
            {"type": "ip", "value": "192.168.1.100", "confidence": "high"},
            {"type": "domain", "value": "example-malicious.com", "confidence": "medium"}
        ],
        "threat_type": "malware",
        "source": "connector_test"
    }
    
    threat_intel_result = await process_threat_intel_tool.execute(
        workflow_id=workflow_id,
        threat_data=test_threat_data
    )
    threat_intelligence = threat_intel_result.result

    print("Type of returned threat_intelligence:", type(threat_intelligence))
    print(f"Threat intelligence preview: {str(threat_intelligence)[:200]}")

    assert threat_intelligence is not None, "threat_intelligence should not be None"
    
    if isinstance(threat_intelligence, dict):
        expected_fields = ["processing_id", "status", "enriched_indicators", "automated_actions", "risk_score"]
        present_fields = [field for field in expected_fields if field in threat_intelligence]
        
        if len(present_fields) > 0:
            print(f"Threat intelligence contains these fields: {', '.join(present_fields)}")
            
            if "status" in threat_intelligence:
                valid_statuses = ["processed", "processing", "enriched", "failed"]
                assert threat_intelligence["status"] in valid_statuses, f"Processing status should be valid"
            
            if "enriched_indicators" in threat_intelligence:
                indicators = threat_intelligence["enriched_indicators"]
                assert isinstance(indicators, list), "Enriched indicators should be a list"
            
            if "risk_score" in threat_intelligence:
                risk_score = threat_intelligence["risk_score"]
                assert isinstance(risk_score, (int, float)), "Risk score should be numeric"
                assert 0 <= risk_score <= 100, "Risk score should be between 0 and 100"
        
        print(f"Threat intelligence structure: {threat_intelligence}")
        
    elif isinstance(threat_intelligence, list):
        assert len(threat_intelligence) > 0, "Threat intelligence list should not be empty"
        
        sample_item = threat_intelligence[0]
        assert isinstance(sample_item, dict), "Threat intelligence items should be dictionaries"
        
        item_fields = ["indicator", "enrichment", "threat_score", "actions_taken"]
        present_item_fields = [field for field in item_fields if field in sample_item]
        
        print(f"Threat intelligence items contain these fields: {', '.join(present_item_fields)}")
        print(f"Example threat intelligence item: {sample_item}")
        
    else:
        assert str(threat_intelligence).strip() != "", "Threat intelligence should contain meaningful data"

    print(f"Successfully processed threat intelligence data")

    return True