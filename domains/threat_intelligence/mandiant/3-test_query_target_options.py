# 3-test_query_target_options.py

async def test_threat_actor_enumeration_options(zerg_state=None):
    """Test Mandiant threat actor and campaign enumeration by way of query target options"""
    print("Attempting to authenticate using Mandiant connector")

    assert zerg_state, "this test requires valid zerg_state"

    mandiant_url = zerg_state.get("mandiant_url").get("value")
    mandiant_api_key = zerg_state.get("mandiant_api_key").get("value")
    mandiant_secret_key = zerg_state.get("mandiant_secret_key").get("value")

    from connectors.mandiant.config import MandiantConnectorConfig
    from connectors.mandiant.connector import MandiantConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = MandiantConnectorConfig(
        url=mandiant_url,
        api_key=mandiant_api_key,
        secret_key=mandiant_secret_key,
    )
    assert isinstance(config, ConnectorConfig), "MandiantConnectorConfig should be of type ConnectorConfig"

    connector = MandiantConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MandiantConnector should be of type Connector"

    mandiant_query_target_options = await connector.get_query_target_options()
    assert isinstance(mandiant_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert mandiant_query_target_options, "Failed to retrieve query target options"

    print(f"mandiant query target option definitions: {mandiant_query_target_options.definitions}")
    print(f"mandiant query target option selectors: {mandiant_query_target_options.selectors}")

    return True