# 3-test_query_target_options.py

async def test_vendor_enumeration_options(zerg_state=None):
    """Test UpGuard vendor and domain enumeration by way of query target options"""
    print("Attempting to authenticate using UpGuard connector")

    assert zerg_state, "this test requires valid zerg_state"

    upguard_url = zerg_state.get("upguard_url").get("value")
    upguard_api_key = zerg_state.get("upguard_api_key").get("value")

    from connectors.upguard.config import UpGuardConnectorConfig
    from connectors.upguard.connector import UpGuardConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = UpGuardConnectorConfig(
        url=upguard_url,
        api_key=upguard_api_key,
    )
    assert isinstance(config, ConnectorConfig), "UpGuardConnectorConfig should be of type ConnectorConfig"

    connector = UpGuardConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "UpGuardConnector should be of type Connector"

    upguard_query_target_options = await connector.get_query_target_options()
    assert isinstance(upguard_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert upguard_query_target_options, "Failed to retrieve query target options"

    print(f"upguard query target option definitions: {upguard_query_target_options.definitions}")
    print(f"upguard query target option selectors: {upguard_query_target_options.selectors}")

    return True