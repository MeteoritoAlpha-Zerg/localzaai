# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing signal connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    signal_api_url = zerg_state.get("signal_api_url").get("value")
    signal_phone_number = zerg_state.get("signal_phone_number").get("value")
    signal_api_key = zerg_state.get("signal_api_key").get("value")

    from connectors.signal.config import SignalConnectorConfig
    from connectors.signal.connector import SignalConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = SignalConnectorConfig(
        api_url=signal_api_url,
        phone_number=signal_phone_number,
        api_key=signal_api_key,
    )
    assert isinstance(config, ConnectorConfig), "SignalConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = SignalConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SignalConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True