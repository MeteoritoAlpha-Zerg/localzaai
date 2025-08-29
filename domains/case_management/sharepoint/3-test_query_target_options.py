# 3-test_query_target_options.py

async def test_site_enumeration_options(zerg_state=None):
    """Test SharePoint site enumeration by way of query target options"""

    from pydantic import SecretStr

    print("Attempting to authenticate using SharePoint connector")

    assert zerg_state, "this test requires valid zerg_state"

    sharepoint_url = zerg_state.get("sharepoint_url").get("value")
    sharepoint_client_id = zerg_state.get("sharepoint_client_id").get("value")
    sharepoint_client_secret = zerg_state.get("sharepoint_client_secret").get("value")
    sharepoint_tenant_id = zerg_state.get("sharepoint_tenant_id").get("value")

    from connectors.sharepoint.config import SharePointConnectorConfig
    from connectors.sharepoint.connector import SharePointConnector
    from connectors.sharepoint.target import SharePointTarget

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SharePointConnectorConfig(
        url=sharepoint_url,
        client_id=sharepoint_client_id,
        client_secret=sharepoint_client_secret,
        tenant_id=sharepoint_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "SharePointConnectorConfig should be of type ConnectorConfig"

    connector = SharePointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SharePointConnectorConfig should be of type ConnectorConfig"

    sharepoint_query_target_options = await connector.get_query_target_options()
    assert isinstance(sharepoint_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert sharepoint_query_target_options, "Failed to retrieve query target options"

    # TODO: what else do we want to do here
    print(f"sharepoint query target option definitions: {sharepoint_query_target_options.definitions}")
    print(f"sharepoint query target option selectors: {sharepoint_query_target_options.selectors}")

    return True