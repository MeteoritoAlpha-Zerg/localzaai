# 3-test_query_target_options.py

async def test_data_type_enumeration_options(zerg_state=None):
    """Test Digital Envoy data type and intelligence feed enumeration by way of query target options"""
    print("Attempting to authenticate using Digital Envoy connector")

    assert zerg_state, "this test requires valid zerg_state"

    digital_envoy_api_key = zerg_state.get("digital_envoy_api_key").get("value")
    digital_envoy_api_secret = zerg_state.get("digital_envoy_api_secret").get("value")
    digital_envoy_base_url = zerg_state.get("digital_envoy_base_url").get("value")
    digital_envoy_api_version = zerg_state.get("digital_envoy_api_version").get("value")

    from connectors.digital_envoy.config import DigitalEnvoyConnectorConfig
    from connectors.digital_envoy.connector import DigitalEnvoyConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = DigitalEnvoyConnectorConfig(
        api_key=digital_envoy_api_key,
        api_secret=digital_envoy_api_secret,
        base_url=digital_envoy_base_url,
        api_version=digital_envoy_api_version,
    )
    assert isinstance(config, ConnectorConfig), "DigitalEnvoyConnectorConfig should be of type ConnectorConfig"

    connector = DigitalEnvoyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DigitalEnvoyConnector should be of type Connector"

    digital_envoy_query_target_options = await connector.get_query_target_options()
    assert isinstance(digital_envoy_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert digital_envoy_query_target_options, "Failed to retrieve query target options"

    print(f"digital envoy query target option definitions: {digital_envoy_query_target_options.definitions}")
    print(f"digital envoy query target option selectors: {digital_envoy_query_target_options.selectors}")

    return True