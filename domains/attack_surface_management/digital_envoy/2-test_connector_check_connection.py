# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing digital envoy connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    digital_envoy_api_key = zerg_state.get("digital_envoy_api_key").get("value")
    digital_envoy_api_secret = zerg_state.get("digital_envoy_api_secret").get("value")
    digital_envoy_base_url = zerg_state.get("digital_envoy_base_url").get("value")
    digital_envoy_api_version = zerg_state.get("digital_envoy_api_version").get("value")

    from connectors.digital_envoy.config import DigitalEnvoyConnectorConfig
    from connectors.digital_envoy.connector import DigitalEnvoyConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = DigitalEnvoyConnectorConfig(
        api_key=digital_envoy_api_key,
        api_secret=digital_envoy_api_secret,
        base_url=digital_envoy_base_url,
        api_version=digital_envoy_api_version,
    )
    assert isinstance(config, ConnectorConfig), "DigitalEnvoyConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = DigitalEnvoyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DigitalEnvoyConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True