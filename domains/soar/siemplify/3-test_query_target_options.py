# 3-test_query_target_options.py

async def test_environment_enumeration_options(zerg_state=None):
    """Test Siemplify environment enumeration by way of query target options"""
    print("Attempting to authenticate using Siemplify (Chronicle SOAR) connector")

    assert zerg_state, "this test requires valid zerg_state"

    siemplify_server_url = zerg_state.get("siemplify_server_url").get("value")
    siemplify_api_token = zerg_state.get("siemplify_api_token").get("value")
    siemplify_user_name = zerg_state.get("siemplify_user_name").get("value")

    from connectors.siemplify.config import SimemplifyConnectorConfig
    from connectors.siemplify.connector import SimemplifyConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SimemplifyConnectorConfig(
        server_url=siemplify_server_url,
        api_token=siemplify_api_token,
        user_name=siemplify_user_name,
    )
    assert isinstance(config, ConnectorConfig), "SimemplifyConnectorConfig should be of type ConnectorConfig"

    connector = SimemplifyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SimemplifyConnector should be of type Connector"

    siemplify_query_target_options = await connector.get_query_target_options()
    assert isinstance(siemplify_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert siemplify_query_target_options, "Failed to retrieve query target options"

    print(f"Siemplify query target option definitions: {siemplify_query_target_options.definitions}")
    print(f"Siemplify query target option selectors: {siemplify_query_target_options.selectors}")

    return True