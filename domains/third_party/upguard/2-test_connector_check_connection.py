# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing upguard connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    upguard_url = zerg_state.get("upguard_url").get("value")
    upguard_api_key = zerg_state.get("upguard_api_key").get("value")

    from connectors.upguard.config import UpGuardConnectorConfig
    from connectors.upguard.connector import UpGuardConnector
    from connectors.config import ConnectorConfig
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

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True