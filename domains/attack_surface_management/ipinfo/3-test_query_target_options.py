# 3-test_query_target_options.py

async def test_data_service_enumeration_options(zerg_state=None):
    """Test IPInfo data service and intelligence feed enumeration by way of query target options"""
    print("Attempting to authenticate using IPInfo connector")

    assert zerg_state, "this test requires valid zerg_state"

    ipinfo_api_token = zerg_state.get("ipinfo_api_token").get("value")
    ipinfo_base_url = zerg_state.get("ipinfo_base_url").get("value")
    ipinfo_api_version = zerg_state.get("ipinfo_api_version").get("value")

    from connectors.ipinfo.config import IPInfoConnectorConfig
    from connectors.ipinfo.connector import IPInfoConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = IPInfoConnectorConfig(
        api_token=ipinfo_api_token,
        base_url=ipinfo_base_url,
        api_version=ipinfo_api_version,
    )
    assert isinstance(config, ConnectorConfig), "IPInfoConnectorConfig should be of type ConnectorConfig"

    connector = IPInfoConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "IPInfoConnector should be of type Connector"

    ipinfo_query_target_options = await connector.get_query_target_options()
    assert isinstance(ipinfo_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert ipinfo_query_target_options, "Failed to retrieve query target options"

    print(f"ipinfo query target option definitions: {ipinfo_query_target_options.definitions}")
    print(f"ipinfo query target option selectors: {ipinfo_query_target_options.selectors}")

    return True