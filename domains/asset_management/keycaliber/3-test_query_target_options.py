# 3-test_query_target_options.py

async def test_asset_enumeration_options(zerg_state=None):
    """Test Key Caliber asset enumeration by way of query target options"""
    print("Attempting to authenticate using Key Caliber connector")

    assert zerg_state, "this test requires valid zerg_state"

    keycaliber_host = zerg_state.get("keycaliber_host").get("value")
    keycaliber_api_key = zerg_state.get("keycaliber_api_key").get("value")

    from connectors.keycaliber.config import KeyCaliberConnectorConfig
    from connectors.keycaliber.connector import KeyCaliberConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = KeyCaliberConnectorConfig(
        host=keycaliber_host,
        api_key=keycaliber_api_key,
    )
    assert isinstance(config, ConnectorConfig), "KeyCaliberConnectorConfig should be of type ConnectorConfig"

    connector = KeyCaliberConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "KeyCaliberConnector should be of type Connector"

    keycaliber_query_target_options = await connector.get_query_target_options()
    assert isinstance(keycaliber_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert keycaliber_query_target_options, "Failed to retrieve query target options"

    print(f"keycaliber query target option definitions: {keycaliber_query_target_options.definitions}")
    print(f"keycaliber query target option selectors: {keycaliber_query_target_options.selectors}")

    return True