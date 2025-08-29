# 3-test_query_target_options.py

async def test_organization_enumeration_options(zerg_state=None):
    """Test Hubble organization and asset group enumeration by way of query target options"""
    print("Attempting to authenticate using Hubble connector")

    assert zerg_state, "this test requires valid zerg_state"

    hubble_url = zerg_state.get("hubble_url").get("value")
    hubble_api_key = zerg_state.get("hubble_api_key", {}).get("value")
    hubble_client_id = zerg_state.get("hubble_client_id", {}).get("value")
    hubble_client_secret = zerg_state.get("hubble_client_secret", {}).get("value")

    from connectors.hubble.config import HubbleConnectorConfig
    from connectors.hubble.connector import HubbleConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
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

    connector = HubbleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "HubbleConnector should be of type Connector"

    hubble_query_target_options = await connector.get_query_target_options()
    assert isinstance(hubble_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert hubble_query_target_options, "Failed to retrieve query target options"

    print(f"hubble query target option definitions: {hubble_query_target_options.definitions}")
    print(f"hubble query target option selectors: {hubble_query_target_options.selectors}")

    return True