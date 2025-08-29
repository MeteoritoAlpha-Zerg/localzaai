# 3-test_query_target_options.py

async def test_domain_enumeration_options(zerg_state=None):
    """Test Devo domain and data table enumeration by way of query target options"""
    print("Attempting to authenticate using Devo connector")

    assert zerg_state, "this test requires valid zerg_state"

    devo_url = zerg_state.get("devo_url").get("value")
    devo_api_key = zerg_state.get("devo_api_key", {}).get("value")
    devo_api_secret = zerg_state.get("devo_api_secret", {}).get("value")
    devo_oauth_token = zerg_state.get("devo_oauth_token", {}).get("value")
    devo_domain = zerg_state.get("devo_domain").get("value")

    from connectors.devo.config import DevoConnectorConfig
    from connectors.devo.connector import DevoConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    # initialize the connector config - prefer OAuth token over API key/secret
    if devo_oauth_token:
        config = DevoConnectorConfig(
            url=devo_url,
            oauth_token=devo_oauth_token,
            default_domain=devo_domain,
        )
    elif devo_api_key and devo_api_secret:
        config = DevoConnectorConfig(
            url=devo_url,
            api_key=devo_api_key,
            api_secret=devo_api_secret,
            default_domain=devo_domain,
        )
    else:
        raise Exception("Either devo_oauth_token or both devo_api_key and devo_api_secret must be provided")

    assert isinstance(config, ConnectorConfig), "DevoConnectorConfig should be of type ConnectorConfig"

    connector = DevoConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DevoConnector should be of type Connector"

    devo_query_target_options = await connector.get_query_target_options()
    assert isinstance(devo_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert devo_query_target_options, "Failed to retrieve query target options"

    print(f"devo query target option definitions: {devo_query_target_options.definitions}")
    print(f"devo query target option selectors: {devo_query_target_options.selectors}")

    return True