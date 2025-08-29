# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing sumologic connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    sumologic_url = zerg_state.get("sumologic_url").get("value")
    sumologic_access_id = zerg_state.get("sumologic_access_id").get("value")
    sumologic_access_key = zerg_state.get("sumologic_access_key").get("value")

    from connectors.sumologic.config import SumoLogicConnectorConfig
    from connectors.sumologic.connector import SumoLogicConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = SumoLogicConnectorConfig(
        url=sumologic_url,
        access_id=sumologic_access_id,
        access_key=sumologic_access_key,
    )
    assert isinstance(config, ConnectorConfig), "SumoLogicConnectorConfig should be of type ConnectorConfig"

    connector = SumoLogicConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SumoLogicConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True