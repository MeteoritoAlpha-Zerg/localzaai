# 6-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Acalvio threat intelligence insights retrieval"""
    print("Attempting to authenticate using Acalvio connector")

    assert zerg_state, "this test requires valid zerg_state"

    acalvio_api_url = zerg_state.get("acalvio_api_url").get("value")
    acalvio_api_key = zerg_state.get("acalvio_api_key").get("value")
    acalvio_username = zerg_state.get("acalvio_username").get("value")
    acalvio_password = zerg_state.get("acalvio_password").get("value")
    acalvio_tenant_id = zerg_state.get("acalvio_tenant_id").get("value")

    from connectors.acalvio.config import AcalvioConnectorConfig
    from connectors.acalvio.connector import AcalvioConnector
    from connectors.acalvio.tools import AcalvioConnectorTools, GetThreatIntelligenceInput
    from connectors.acalvio.target import AcalvioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

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

    # set up the target (no specific targeting needed for threat intelligence)
    target = AcalvioTarget()
    assert isinstance(target, ConnectorTargetInterface), "AcalvioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_threat_intelligence tool
    get_threat_intelligence_tool = next(tool for tool in tools if tool.name == "get_threat_intelligence")
    threat_intelligence_result = await get_threat_intelligence_tool.execute()
    threat_intelligence = threat_intelligence_result.result

    print("Type of returned threat_intelligence:", type(threat_intelligence))
    print(f"Threat intelligence keys: {list(threat_intelligence.keys()) if isinstance(threat_intelligence, dict) else 'Not a dict'}")

    # Verify that threat_intelligence is a dictionary
    assert isinstance(threat_intelligence, dict), "threat_intelligence should be a dict"
    
    # Verify essential threat intelligence fields
    assert "summary" in threat_intelligence, "Threat intelligence should have a 'summary' field"
    assert "attack_patterns" in threat_intelligence, "Threat intelligence should have an 'attack_patterns' field"
    assert "threat_actors" in threat_intelligence, "Threat intelligence should have a 'threat_actors' field"
    
    # Verify attack patterns structure
    attack_patterns = threat_intelligence["attack_patterns"]
    assert isinstance(attack_patterns, list), "attack_patterns should be a list"
    
    if len(attack_patterns) > 0:
        # Check structure of attack patterns
        for pattern in attack_patterns[:3]:  # Check first 3 patterns
            assert "technique_id" in pattern, "Each attack pattern should have a 'technique_id'"
            assert "technique_name" in pattern, "Each attack pattern should have a 'technique_name'"
            assert "frequency" in pattern, "Each attack pattern should have a 'frequency'"
            
            # Check for MITRE ATT&CK mapping
            if "mitre_technique" in pattern:
                mitre = pattern["mitre_technique"]
                assert "id" in mitre, "MITRE technique should have an 'id'"
                assert "name" in mitre, "MITRE technique should have a 'name'"
    
    # Verify threat actors structure
    threat_actors = threat_intelligence["threat_actors"]
    assert isinstance(threat_actors, list), "threat_actors should be a list"
    
    if len(threat_actors) > 0:
        # Check structure of threat actors
        for actor in threat_actors[:3]:  # Check first 3 actors
            assert "actor_id" in actor, "Each threat actor should have an 'actor_id'"
            assert "behavior_profile" in actor, "Each threat actor should have a 'behavior_profile'"
            
            # Check for optional fields
            optional_actor_fields = ["source_countries", "target_industries", "attack_sophistication", "tools_used"]
            present_actor_fields = [field for field in optional_actor_fields if field in actor]
            print(f"Threat actor {actor['actor_id']} contains these fields: {', '.join(present_actor_fields)}")
    
    # Check for additional intelligence fields
    intelligence_fields = ["ttps", "iocs", "recommendations", "trending_threats", "risk_assessment"]
    present_intelligence = [field for field in intelligence_fields if field in threat_intelligence]
    
    print(f"Threat intelligence contains these additional fields: {', '.join(present_intelligence)}")
    
    # Verify summary information
    summary = threat_intelligence["summary"]
    assert isinstance(summary, dict), "summary should be a dict"
    
    summary_fields = ["total_alerts", "unique_attack_patterns", "threat_level", "time_period"]
    for field in summary_fields:
        if field in summary:
            print(f"Summary contains {field}: {summary[field]}")
    
    # Log intelligence overview
    print(f"Threat intelligence overview:")
    print(f"  - Attack patterns: {len(attack_patterns)}")
    print(f"  - Threat actors: {len(threat_actors)}")
    print(f"  - Additional intelligence fields: {len(present_intelligence)}")

    print(f"Successfully retrieved and validated Acalvio threat intelligence")

    return True