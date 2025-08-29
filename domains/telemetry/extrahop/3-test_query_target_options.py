# 3-test_query_target_options.py

async def test_sensor_network_enumeration_options(zerg_state=None):
    """Test ExtraHop sensor network enumeration by way of query target options"""
    print("Attempting to authenticate using ExtraHop connector")

    assert zerg_state, "this test requires valid zerg_state"

    extrahop_server_url = zerg_state.get("extrahop_server_url").get("value")
    extrahop_api_key = zerg_state.get("extrahop_api_key").get("value")
    extrahop_api_secret = zerg_state.get("extrahop_api_secret").get("value")

    from connectors.extrahop.config import ExtraHopConnectorConfig
    from connectors.extrahop.connector import ExtraHopConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = ExtraHopConnectorConfig(
        server_url=extrahop_server_url,
        api_key=extrahop_api_key,
        api_secret=extrahop_api_secret,
    )
    assert isinstance(config, ConnectorConfig), "ExtraHopConnectorConfig should be of type ConnectorConfig"

    connector = ExtraHopConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ExtraHopConnector should be of type Connector"

    extrahop_query_target_options = await connector.get_query_target_options()
    assert isinstance(extrahop_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert extrahop_query_target_options, "Failed to retrieve query target options"

    print(f"ExtraHop query target option definitions: {extrahop_query_target_options.definitions}")
    print(f"ExtraHop query target option selectors: {extrahop_query_target_options.selectors}")

    return True