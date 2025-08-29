# 3-test_query_target_options.py

async def test_label_enumeration_options(zerg_state=None):
    """Test Gmail label enumeration by way of query target options"""
    print("Attempting to authenticate using Gmail connector")

    assert zerg_state, "this test requires valid zerg_state"

    gmail_oauth_client_id = zerg_state.get("gmail_oauth_client_id").get("value")
    gmail_oauth_client_secret = zerg_state.get("gmail_oauth_client_secret").get("value")
    gmail_oauth_refresh_token = zerg_state.get("gmail_oauth_refresh_token").get("value")
    gmail_api_base_url = zerg_state.get("gmail_api_base_url").get("value")
    gmail_api_version = zerg_state.get("gmail_api_version").get("value")

    from connectors.gmail.config import GmailConnectorConfig
    from connectors.gmail.connector import GmailConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = GmailConnectorConfig(
        oauth_client_id=gmail_oauth_client_id,
        oauth_client_secret=gmail_oauth_client_secret,
        oauth_refresh_token=gmail_oauth_refresh_token,
        api_base_url=gmail_api_base_url,
        api_version=gmail_api_version,
    )
    assert isinstance(config, ConnectorConfig), "GmailConnectorConfig should be of type ConnectorConfig"

    connector = GmailConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GmailConnector should be of type Connector"

    gmail_query_target_options = await connector.get_query_target_options()
    assert isinstance(gmail_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert gmail_query_target_options, "Failed to retrieve query target options"

    print(f"gmail query target option definitions: {gmail_query_target_options.definitions}")
    print(f"gmail query target option selectors: {gmail_query_target_options.selectors}")

    return True