# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to Splunk Phantom APIs"""
    print("Testing Splunk Phantom connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    splunk_phantom_api_url = zerg_state.get("splunk_phantom_api_url").get("value")
    splunk_phantom_api_token = zerg_state.get("splunk_phantom_api_token").get("value")

    from connectors.splunk_phantom.config import SplunkPhantomConnectorConfig
    from connectors.splunk_phantom.connector import SplunkPhantomConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = SplunkPhantomConnectorConfig(
        api_url=splunk_phantom_api_url,
        api_token=splunk_phantom_api_token,
    )
    assert isinstance(config, ConnectorConfig), "SplunkPhantomConnectorConfig should be of type ConnectorConfig"

    connector = SplunkPhantomConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SplunkPhantomConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True