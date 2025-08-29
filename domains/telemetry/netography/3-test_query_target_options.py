# 3-test_query_target_options.py

async def test_sensor_data_source_enumeration_options(zerg_state=None):
    """Test Netography sensor and data source enumeration by way of query target options"""
    print("Attempting to authenticate using Netography connector")

    assert zerg_state, "this test requires valid zerg_state"

    netography_api_token = zerg_state.get("netography_api_token").get("value")
    netography_base_url = zerg_state.get("netography_base_url").get("value")
    netography_tenant_id = zerg_state.get("netography_tenant_id").get("value")

    from connectors.netography.config import NetographyConnectorConfig
    from connectors.netography.connector import NetographyConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = NetographyConnectorConfig(
        api_token=netography_api_token,
        base_url=netography_base_url,
        tenant_id=netography_tenant_id,
    )
    assert isinstance(config, ConnectorConfig), "NetographyConnectorConfig should be of type ConnectorConfig"

    connector = NetographyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "NetographyConnector should be of type Connector"

    netography_query_target_options = await connector.get_query_target_options()
    assert isinstance(netography_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert netography_query_target_options, "Failed to retrieve query target options"

    print(f"Netography query target option definitions: {netography_query_target_options.definitions}")
    print(f"Netography query target option selectors: {netography_query_target_options.selectors}")

    return True