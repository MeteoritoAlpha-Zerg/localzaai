# 3-test_query_target_options.py

async def test_asset_category_enumeration_options(zerg_state=None):
    """Test Xpanse asset category and exposure type enumeration by way of query target options"""
    print("Attempting to authenticate using Xpanse connector")

    assert zerg_state, "this test requires valid zerg_state"

    xpanse_api_url = zerg_state.get("xpanse_api_url").get("value")
    xpanse_api_key = zerg_state.get("xpanse_api_key").get("value")
    xpanse_api_key_id = zerg_state.get("xpanse_api_key_id").get("value")
    xpanse_tenant_id = zerg_state.get("xpanse_tenant_id").get("value")
    xpanse_api_version = zerg_state.get("xpanse_api_version").get("value")

    from connectors.xpanse.config import XpanseConnectorConfig
    from connectors.xpanse.connector import XpanseConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = XpanseConnectorConfig(
        api_url=xpanse_api_url,
        api_key=xpanse_api_key,
        api_key_id=xpanse_api_key_id,
        tenant_id=xpanse_tenant_id,
        api_version=xpanse_api_version,
    )
    assert isinstance(config, ConnectorConfig), "XpanseConnectorConfig should be of type ConnectorConfig"

    connector = XpanseConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "XpanseConnector should be of type Connector"

    xpanse_query_target_options = await connector.get_query_target_options()
    assert isinstance(xpanse_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert xpanse_query_target_options, "Failed to retrieve query target options"

    print(f"xpanse query target option definitions: {xpanse_query_target_options.definitions}")
    print(f"xpanse query target option selectors: {xpanse_query_target_options.selectors}")

    return True