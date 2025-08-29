# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing mandiant connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    mandiant_url = zerg_state.get("mandiant_url").get("value")
    mandiant_api_key = zerg_state.get("mandiant_api_key").get("value")
    mandiant_secret_key = zerg_state.get("mandiant_secret_key").get("value")

    from connectors.mandiant.config import MandiantConnectorConfig
    from connectors.mandiant.connector import MandiantConnector
    from connectors.config import ConnectorConfig
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

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True