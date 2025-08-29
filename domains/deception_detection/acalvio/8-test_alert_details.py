# 8-test_alert_details.py

async def test_alert_details(zerg_state=None):
    """Test Acalvio detailed alert information retrieval including behavioral analysis"""
    print("Attempting to authenticate using Acalvio connector")

    assert zerg_state, "this test requires valid zerg_state"

    acalvio_api_url = zerg_state.get("acalvio_api_url").get("value")
    acalvio_api_key = zerg_state.get("acalvio_api_key").get("value")
    acalvio_username = zerg_state.get("acalvio_username").get("value")
    acalvio_password = zerg_state.get("acalvio_password").get("value")
    acalvio_tenant_id = zerg_state.get("acalvio_tenant_id").get("value")

    from connectors.acalvio.config import AcalvioConnectorConfig
    from connectors.acalvio.connector import AcalvioConnector
    from connectors.acalvio.tools import AcalvioConnectorTools, GetAlertDetailsInput
    from connectors.acalvio.target import AcalvioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = AcalvioConnectorConfig(
        api_url=acalvio_api_url,
        api_key=acalvio_api_key,
        username=acalvio_username,
        password=acalvio_password,
        tenant_id=acalvio_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "AcalvioConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = AcalvioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "AcalvioConnectorConfig should be of type ConnectorConfig"

    # get query target options
    acalvio_query_target_options = await connector.get_query_target_options()
    assert isinstance(acalvio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select environment to target
    environment_selector = None
    for selector in acalvio_query_target_options.selectors:
        if selector.type == 'environment_ids':  
            environment_selector = selector
            break

    assert environment_selector, "failed to retrieve environment selector from query target options"

    assert isinstance(environment_selector.values, list), "environment_selector values must be a list"
    environment_id = environment_selector.values[0] if environment_selector.values else None
    print(f"Selecting environment id: {environment_id}")

    assert environment_id, f"failed to retrieve environment id from environment selector"

    # set up the target with environment id
    target = AcalvioTarget(environment_ids=[environment_id])
    assert isinstance(target, ConnectorTargetInterface), "AcalvioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # First get a list of alerts to find one to retrieve details for
    get_acalvio_alerts_tool = next(tool for tool in tools if tool.name == "get_acalvio_alerts")
    acalvio_alerts_result = await get_acalvio_alerts_tool.execute(environment_id=environment_id)
    acalvio_alerts = acalvio_alerts_result.result

    assert isinstance(acalvio_alerts, list), "acalvio_alerts should be a list"
    assert len(acalvio_alerts) > 0, "acalvio_alerts should not be empty"

    # Use the first alert for details retrieval test
    test_alert = acalvio_alerts[0]
    alert_id = test_alert["id"]
    print(f"Testing details retrieval for alert ID: {alert_id}")

    # grab the get_alert_details tool and execute it with alert ID
    get_alert_details_tool = next(tool for tool in tools if tool.name == "get_alert_details")
    alert_details_result = await get_alert_details_tool.execute(alert_id=alert_id)
    alert_details = alert_details_result.result

    print("Type of returned alert_details:", type(alert_details))
    print(f"Alert details keys: {list(alert_details.keys()) if isinstance(alert_details, dict) else 'Not a dict'}")

    # Verify that alert_details is a dictionary
    assert isinstance(alert_details, dict), "alert_details should be a dict"
    
    # Verify essential alert details fields
    assert "id" in alert_details, "Alert details should have an 'id' field"
    assert alert_details["id"] == alert_id, "Alert details ID should match requested ID"
    
    assert "timestamp" in alert_details, "Alert details should have a 'timestamp' field"
    assert "severity" in alert_details, "Alert details should have a 'severity' field"
    assert "alert_type" in alert_details, "Alert details should have an 'alert_type' field"
    assert "description" in alert_details, "Alert details should have a 'description' field"
    
    # Verify behavioral analysis fields
    behavior_fields = ["attacker_behavior", "attack_timeline", "techniques_used", "indicators"]
    present_behavior = [field for field in behavior_fields if field in alert_details]
    
    print(f"Alert contains these behavioral analysis fields: {', '.join(present_behavior)}")
    
    # Verify attacker behavior analysis if present
    if "attacker_behavior" in alert_details:
        behavior = alert_details["attacker_behavior"]
        assert isinstance(behavior, dict), "attacker_behavior should be a dict"
        
        behavior_analysis_fields = ["tactics", "techniques", "procedures", "sophistication_level", "persistence_indicators"]
        present_analysis = [field for field in behavior_analysis_fields if field in behavior]
        print(f"Attacker behavior analysis contains: {', '.join(present_analysis)}")
    
    # Verify attack timeline if present
    if "attack_timeline" in alert_details:
        timeline = alert_details["attack_timeline"]
        assert isinstance(timeline, list), "attack_timeline should be a list"
        
        if len(timeline) > 0:
            for event in timeline[:3]:  # Check first 3 events
                assert "timestamp" in event, "Each timeline event should have a 'timestamp'"
                assert "action" in event, "Each timeline event should have an 'action'"
    
    # Verify MITRE ATT&CK mapping if present
    if "mitre_techniques" in alert_details:
        techniques = alert_details["mitre_techniques"]
        assert isinstance(techniques, list), "mitre_techniques should be a list"
        
        for technique in techniques:
            assert "technique_id" in technique, "Each MITRE technique should have a 'technique_id'"
            assert "technique_name" in technique, "Each MITRE technique should have a 'technique_name'"
            assert "tactic" in technique, "Each MITRE technique should have a 'tactic'"
    
    # Check for response and remediation fields
    response_fields = ["recommended_actions", "containment_steps", "investigation_notes", "risk_assessment"]
    present_response = [field for field in response_fields if field in alert_details]
    
    print(f"Alert contains these response fields: {', '.join(present_response)}")
    
    # Verify network and system context
    context_fields = ["source_ip", "destination_ip", "affected_assets", "network_flow", "process_details"]
    present_context = [field for field in context_fields if field in alert_details]
    
    print(f"Alert contains these context fields: {', '.join(present_context)}")
    
    # Log detailed alert summary
    print(f"Alert details summary:")
    print(f"  - ID: {alert_details['id']}")
    print(f"  - Severity: {alert_details['severity']}")
    print(f"  - Type: {alert_details['alert_type']}")
    print(f"  - Timestamp: {alert_details['timestamp']}")
    
    if "attacker_behavior" in alert_details:
        behavior = alert_details["attacker_behavior"]
        if "sophistication_level" in behavior:
            print(f"  - Sophistication: {behavior['sophistication_level']}")
    
    if "mitre_techniques" in alert_details:
        print(f"  - MITRE Techniques: {len(alert_details['mitre_techniques'])}")
    
    if "recommended_actions" in alert_details:
        actions = alert_details["recommended_actions"]
        if isinstance(actions, list) and len(actions) > 0:
            print(f"  - Recommended Actions: {len(actions)} action(s)")

    print(f"Successfully retrieved and validated detailed alert information for ID {alert_id}")

    return True