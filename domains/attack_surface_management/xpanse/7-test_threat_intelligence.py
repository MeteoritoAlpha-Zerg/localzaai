# 7-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Xpanse threat intelligence retrieval by way of connector tools"""
    print("Attempting to authenticate using Xpanse connector")

    assert zerg_state, "this test requires valid zerg_state"

    # Config setup
    xpanse_api_url = zerg_state.get("xpanse_api_url").get("value")
    xpanse_api_key = zerg_state.get("xpanse_api_key").get("value")
    xpanse_api_key_id = zerg_state.get("xpanse_api_key_id").get("value")
    xpanse_tenant_id = zerg_state.get("xpanse_tenant_id").get("value")
    xpanse_api_version = zerg_state.get("xpanse_api_version").get("value")

    from connectors.xpanse.config import XpanseConnectorConfig
    from connectors.xpanse.connector import XpanseConnector
    from connectors.xpanse.target import XpanseTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    config = XpanseConnectorConfig(
        api_url=xpanse_api_url, api_key=xpanse_api_key, api_key_id=xpanse_api_key_id,
        tenant_id=xpanse_tenant_id, api_version=xpanse_api_version
    )

    connector = XpanseConnector
    await connector.initialize(config=config, user_id="test_user_id", encryption_key="test_enc_key")

    target = XpanseTarget(threat_categories=["apt_groups", "targeting_intelligence"])
    tools = await connector.get_tools(target=target)
    get_threat_intel_tool = next(tool for tool in tools if tool.name == "get_xpanse_threat_intelligence")
    threat_intel_result = await get_threat_intel_tool.execute(confidence_threshold=70)
    xpanse_threat_intel = threat_intel_result.result

    # Validate results
    assert isinstance(xpanse_threat_intel, list), "xpanse_threat_intel should be a list"
    assert len(xpanse_threat_intel) > 0, "xpanse_threat_intel should not be empty"

    for threat in xpanse_threat_intel[:3]:  # Check first 3 threat intelligence items
        assert "threat_id" in threat, "Each threat should have a 'threat_id' field"
        assert "threat_actor" in threat, "Each threat should have a 'threat_actor' field"
        assert "confidence_level" in threat, "Each threat should have a 'confidence_level' field"
        
        # Validate confidence level
        confidence = threat["confidence_level"]
        assert isinstance(confidence, (int, float)), "Confidence should be numeric"
        assert 0 <= confidence <= 100, f"Confidence should be 0-100: {confidence}"
        
        # Check for attribution and targeting fields
        threat_fields = ["attribution", "targeting_data", "attack_patterns"]
        present_fields = [field for field in threat_fields if field in threat]
        print(f"Threat {threat['threat_id']} contains: {', '.join(present_fields)}")

    print(f"Successfully retrieved {len(xpanse_threat_intel)} Xpanse threat intelligence items")
    return True