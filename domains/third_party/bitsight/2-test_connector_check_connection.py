# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing bitsight connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    bitsight_url = zerg_state.get("bitsight_url").get("value")
    bitsight_api_token = zerg_state.get("bitsight_api_token").get("value")

    from connectors.bitsight.config import BitSightConnectorConfig
    from connectors.bitsight.connector import BitSightConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = BitSightConnectorConfig(
        url=bitsight_url,
        api_token=bitsight_api_token,
    )
    assert isinstance(config, ConnectorConfig), "BitSightConnectorConfig should be of type ConnectorConfig"

    connector = BitSightConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "BitSightConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True