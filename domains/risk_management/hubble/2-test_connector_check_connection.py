# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing hubble connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    hubble_url = zerg_state.get("hubble_url").get("value")
    hubble_api_key = zerg_state.get("hubble_api_key", {}).get("value")
    hubble_client_id = zerg_state.get("hubble_client_id", {}).get("value")
    hubble_client_secret = zerg_state.get("hubble_client_secret", {}).get("value")

    from connectors.hubble.config import HubbleConnectorConfig
    from connectors.hubble.connector import HubbleConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    # initialize the connector config - prefer API key over OAuth
    if hubble_api_key:
        config = HubbleConnectorConfig(
            url=hubble_url,
            api_key=hubble_api_key,
        )
    elif hubble_client_id and hubble_client_secret:
        config = HubbleConnectorConfig(
            url=hubble_url,
            client_id=hubble_client_id,
            client_secret=hubble_client_secret,
        )
    else:
        raise Exception("Either hubble_api_key or both hubble_client_id and hubble_client_secret must be provided")

    assert isinstance(config, ConnectorConfig), "HubbleConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = HubbleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "HubbleConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True