# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing devo connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    devo_url = zerg_state.get("devo_url").get("value")
    devo_api_key = zerg_state.get("devo_api_key", {}).get("value")
    devo_api_secret = zerg_state.get("devo_api_secret", {}).get("value")
    devo_oauth_token = zerg_state.get("devo_oauth_token", {}).get("value")
    devo_domain = zerg_state.get("devo_domain").get("value")

    from connectors.devo.config import DevoConnectorConfig
    from connectors.devo.connector import DevoConnector
    
    from connectors.config import ConnectorConfig
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

    # initialize the connector
    connector = DevoConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DevoConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True