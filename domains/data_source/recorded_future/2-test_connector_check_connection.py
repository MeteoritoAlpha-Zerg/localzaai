# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to Recorded Future APIs"""
    print("Testing Recorded Future connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    rf_api_url = zerg_state.get("recorded_future_api_url").get("value")
    rf_api_token = zerg_state.get("recorded_future_api_token").get("value")

    from connectors.recorded_future.config import RecordedFutureConnectorConfig
    from connectors.recorded_future.connector import RecordedFutureConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = RecordedFutureConnectorConfig(
        api_url=rf_api_url,
        api_token=rf_api_token,
    )
    assert isinstance(config, ConnectorConfig), "RecordedFutureConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = RecordedFutureConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RecordedFutureConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True