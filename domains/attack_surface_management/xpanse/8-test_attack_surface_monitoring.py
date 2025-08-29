# 8-test_attack_surface_monitoring.py

async def test_attack_surface_monitoring(zerg_state=None):
    """Test Xpanse attack surface monitoring and discovery retrieval by way of connector tools"""
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

    target = XpanseTarget(monitoring_scopes=["external_discovery", "attribution_analysis"])
    tools = await connector.get_tools(target=target)
    get_monitoring_tool = next(tool for tool in tools if tool.name == "get_xpanse_monitoring_data")
    monitoring_result = await get_monitoring_tool.execute(time_range="7days")
    xpanse_monitoring = monitoring_result.result

    # Validate results
    assert isinstance(xpanse_monitoring, dict), "xpanse_monitoring should be a dictionary"
    assert len(xpanse_monitoring) > 0, "xpanse_monitoring should not be empty"

    # Check for discovery and monitoring data structure
    assert "discovered_assets" in xpanse_monitoring, "Should contain discovered_assets"
    assert "attribution_data" in xpanse_monitoring, "Should contain attribution_data"

    discovered_assets = xpanse_monitoring["discovered_assets"]
    assert isinstance(discovered_assets, list), "Discovered assets should be a list"

    for asset in discovered_assets[:3]:  # Check first 3 discovered assets
        assert "asset_id" in asset, "Each discovered asset should have an 'asset_id' field"
        assert "discovery_date" in asset, "Each discovered asset should have a 'discovery_date' field"
        assert "attribution_confidence" in asset, "Each discovered asset should have attribution confidence"
        
        # Check for discovery-specific fields
        discovery_fields = ["asset_attribution", "discovery_method", "exposure_timeline"]
        present_fields = [field for field in discovery_fields if field in asset]
        print(f"Discovered asset {asset['asset_id']} contains: {', '.join(present_fields)}")

    attribution_data = xpanse_monitoring["attribution_data"]
    assert isinstance(attribution_data, dict), "Attribution data should be a dictionary"
    
    # Check attribution summary
    attribution_fields = ["total_attributed", "confidence_distribution", "ownership_analysis"]
    present_attribution = [field for field in attribution_fields if field in attribution_data]
    print(f"Attribution analysis contains: {', '.join(present_attribution)}")

    print(f"Successfully retrieved Xpanse monitoring data with {len(discovered_assets)} discovered assets")
    return True