async def test_ticket_enumeration_options(zerg_state=None):
    """Test Zendesk ticket enumeration by way of query target options"""
    print("Attempting to authenticate using Zendesk connector")

    assert zerg_state, "this test requires valid zerg_state"

    zendesk_subdomain = zerg_state.get("zendesk_subdomain").get("value")
    zendesk_email = zerg_state.get("zendesk_email").get("value")
    zendesk_api_token = zerg_state.get("zendesk_api_token").get("value")

    from connectors.zendesk.config import ZendeskConnectorConfig
    from connectors.zendesk.connector import ZendeskConnector
    from connectors.zendesk.target import ZendeskTarget

    config = ZendeskConnectorConfig(
        subdomain=zendesk_subdomain,
        email=zendesk_email,
        api_token=SecretStr(zendesk_api_token)
    )
    connector = ZendeskConnector(config)

    connector_target = ZendeskTarget(config=config)

    zendesk_query_target_options = await connector.get_query_target_options()

    assert zendesk_query_target_options, "Failed to retrieve query target options"

    # TODO: what else do we want to do here
    print(f"zendesk query target option definitions: {zendesk_query_target_options.definitions}")
    print(f"zendesk query target option selectors: {zendesk_query_target_options.selectors}")

    return True