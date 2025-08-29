# 3-test_query_target_options.py

async def test_query_type_data_source_enumeration_options(zerg_state=None):
    """Test GreyNoise query type and data source enumeration by way of query target options"""
    print("Attempting to authenticate using GreyNoise connector")

    assert zerg_state, "this test requires valid zerg_state"

    greynoise_api_key = zerg_state.get("greynoise_api_key").get("value")
    greynoise_base_url = zerg_state.get("greynoise_base_url").get("value")

    from connectors.greynoise.config import GreyNoiseConnectorConfig
    from connectors.greynoise.connector import GreyNoiseConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = GreyNoiseConnectorConfig(
        api_key=greynoise_api_key,
        base_url=greynoise_base_url,
    )
    assert isinstance(config, ConnectorConfig), "GreyNoiseConnectorConfig should be of type ConnectorConfig"

    connector = GreyNoiseConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GreyNoiseConnector should be of type Connector"

    greynoise_query_target_options = await connector.get_query_target_options()
    assert isinstance(greynoise_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert greynoise_query_target_options, "Failed to retrieve query target options"

    print(f"GreyNoise query target option definitions: {greynoise_query_target_options.definitions}")
    print(f"GreyNoise query target option selectors: {greynoise_query_target_options.selectors}")

    return True