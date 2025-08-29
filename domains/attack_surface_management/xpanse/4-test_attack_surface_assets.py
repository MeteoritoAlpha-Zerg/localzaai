# 4-test_attack_surface_assets.py

async def test_attack_surface_assets(zerg_state=None):
    """Test Xpanse attack surface assets retrieval by way of connector tools"""
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
    assert isinstance(config, ConnectorConfig), "XpanseConnectorConfig should be of type ConnectorConfig"

    connector = XpanseConnector
    await connector.initialize(config=config, user_id="test_user_id", encryption_key="test_enc_key")
    assert isinstance(connector, Connector), "XpanseConnector should be of type Connector"

    # Get target options and select asset categories
    xpanse_query_target_options = await connector.get_query_target_options()
    asset_category_selector = next((s for s in xpanse_query_target_options.selectors if s.type == 'asset_categories'), None)
    assert asset_category_selector, "failed to retrieve asset category selector"
    
    asset_categories = asset_category_selector.values[:2] if asset_category_selector.values else None
    assert asset_categories, "failed to retrieve asset categories"
    print(f"Selecting asset categories: {asset_categories}")

    target = XpanseTarget(asset_categories=asset_categories)
    assert isinstance(target, ConnectorTargetInterface), "XpanseTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    get_assets_tool = next(tool for tool in tools if tool.name == "get_xpanse_assets")
    assets_result = await get_assets_tool.execute()
    xpanse_assets = assets_result.result

    # Validate results
    assert isinstance(xpanse_assets, list), "xpanse_assets should be a list"
    assert len(xpanse_assets) > 0, "xpanse_assets should not be empty"

    for asset in xpanse_assets[:3]:  # Check first 3 assets
        assert "asset_id" in asset, "Each asset should have an 'asset_id' field"
        assert "asset_type" in asset, "Each asset should have an 'asset_type' field"
        assert "exposure_status" in asset, "Each asset should have an 'exposure_status' field"
        
        # Validate essential attack surface fields
        essential_fields = ["ip_address", "domain", "service_type", "risk_score"]
        present_fields = [field for field in essential_fields if field in asset]
        print(f"Asset {asset['asset_id']} contains: {', '.join(present_fields)}")

    print(f"Successfully retrieved {len(xpanse_assets)} Xpanse attack surface assets")
    return True