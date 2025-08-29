# 3-test_query_target_options.py

async def test_project_enumeration_options(zerg_state=None):
    """Test Zendesk project enumeration by way of query target options"""
    print("Attempting to authenticate using Zendesk connector")

    assert zerg_state, "this test requires valid zerg_state"

    zendesk_subdomain = zerg_state.get("zendesk_subdomain").get("value")
    zendesk_email = zerg_state.get("zendesk_email").get("value")
    zendesk_api_token = zerg_state.get("zendesk_api_token").get("value")

    from connectors.zendesk.config import ZendeskConnectorConfig
    from connectors.zendesk.connector import ZendeskConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    # initialize the connector config
    config = ZendeskConnectorConfig(
        subdomain=zendesk_subdomain,
        email=zendesk_email,
        api_token=zendesk_api_token,
    )
    assert isinstance(config, ConnectorConfig), "ZendeskConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ZendeskConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ZendeskConnector should be of type Connector"

    query_target_options = await connector.get_query_target_options()
    assert isinstance(query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert query_target_options, "Failed to retrieve query target options"

    print(f"zendesk query target option definitions: {query_target_options.definitions}")
    print(f"zendesk query target option selectors: {query_target_options.selectors}")

    return True