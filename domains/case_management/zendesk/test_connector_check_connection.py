def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing zendesk connector connection")

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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

    connection_valid = loop.run_until_complete(connector.check_connection())
    loop.close()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True