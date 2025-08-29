# 5-test_security_incidents.py

async def test_security_incidents(zerg_state=None):
    """Test Xpanse security incidents retrieval by way of connector tools"""
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
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = XpanseConnectorConfig(
        api_url=xpanse_api_url, api_key=xpanse_api_key, api_key_id=xpanse_api_key_id,
        tenant_id=xpanse_tenant_id, api_version=xpanse_api_version
    )

    connector = XpanseConnector
    await connector.initialize(config=config, user_id="test_user_id", encryption_key="test_enc_key")

    # Get target options and select incident types
    xpanse_query_target_options = await connector.get_query_target_options()
    incident_type_selector = next((s for s in xpanse_query_target_options.selectors if s.type == 'incident_types'), None)
    
    incident_types = incident_type_selector.values[:2] if incident_type_selector and incident_type_selector.values else ["exposure_alert"]
    print(f"Selecting incident types: {incident_types}")

    target = XpanseTarget(incident_types=incident_types)
    tools = await connector.get_tools(target=target)
    get_incidents_tool = next(tool for tool in tools if tool.name == "get_xpanse_incidents")
    incidents_result = await get_incidents_tool.execute(severity_filter="Medium")
    xpanse_incidents = incidents_result.result

    # Validate results
    assert isinstance(xpanse_incidents, list), "xpanse_incidents should be a list"
    assert len(xpanse_incidents) > 0, "xpanse_incidents should not be empty"

    for incident in xpanse_incidents[:3]:  # Check first 3 incidents
        assert "incident_id" in incident, "Each incident should have an 'incident_id' field"
        assert "severity" in incident, "Each incident should have a 'severity' field"
        assert "status" in incident, "Each incident should have a 'status' field"
        
        # Validate severity levels
        valid_severities = ["Low", "Medium", "High", "Critical"]
        assert incident["severity"] in valid_severities, f"Severity should be valid: {incident['severity']}"
        
        # Check for exposure-specific fields
        exposure_fields = ["affected_assets", "exposure_type", "detection_date"]
        present_fields = [field for field in exposure_fields if field in incident]
        print(f"Incident {incident['incident_id']} contains: {', '.join(present_fields)}")

    print(f"Successfully retrieved {len(xpanse_incidents)} Xpanse security incidents")
    return True