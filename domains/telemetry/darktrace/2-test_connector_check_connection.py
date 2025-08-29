# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing darktrace connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    darktrace_url = zerg_state.get("darktrace_url").get("value")
    darktrace_public_token = zerg_state.get("darktrace_public_token").get("value")
    darktrace_private_token = zerg_state.get("darktrace_private_token").get("value")

    from connectors.darktrace.config import DarktraceConnectorConfig
    from connectors.darktrace.connector import DarktraceConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = DarktraceConnectorConfig(
        url=darktrace_url,
        public_token=darktrace_public_token,
        private_token=darktrace_private_token,
    )
    assert isinstance(config, ConnectorConfig), "DarktraceConnectorConfig should be of type ConnectorConfig"

    connector = DarktraceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DarktraceConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True