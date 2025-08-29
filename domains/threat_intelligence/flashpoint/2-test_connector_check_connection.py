# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to Flashpoint APIs"""
    print("Testing Flashpoint connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    flashpoint_api_url = zerg_state.get("flashpoint_api_url").get("value")
    flashpoint_api_key = zerg_state.get("flashpoint_api_key").get("value")

    from connectors.flashpoint.config import FlashpointConnectorConfig
    from connectors.flashpoint.connector import FlashpointConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = FlashpointConnectorConfig(
        api_url=flashpoint_api_url,
        api_key=flashpoint_api_key,
    )
    assert isinstance(config, ConnectorConfig), "FlashpointConnectorConfig should be of type ConnectorConfig"

    connector = FlashpointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "FlashpointConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True