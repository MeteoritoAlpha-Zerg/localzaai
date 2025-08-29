def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing salesforce connector connection")

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    assert zerg_state, "this test requires valid zerg_state"

    salesforce_username = zerg_state.get("salesforce_username").get("value")
    salesforce_password = zerg_state.get("salesforce_password").get("value")
    salesforce_security_token = zerg_state.get("salesforce_security_token").get("value")
    salesforce_consumer_key = zerg_state.get("salesforce_consumer_key").get("value")
    salesforce_consumer_secret = zerg_state.get("salesforce_consumer_secret").get("value")
    salesforce_domain = zerg_state.get("salesforce_domain").get("value")

    from connectors.salesforce.config import SalesforceConnectorConfig
    from connectors.salesforce.connector import SalesforceConnector
    from connectors.salesforce.target import SalesforceTarget

    config = SalesforceConnectorConfig(
        username=salesforce_username,
        password=SecretStr(salesforce_password),
        security_token=SecretStr(salesforce_security_token),
        consumer_key=salesforce_consumer_key,
        consumer_secret=SecretStr(salesforce_consumer_secret),
        domain=salesforce_domain
    )
    connector = SalesforceConnector(config)

    connection_valid = loop.run_until_complete(connector.check_connection())
    loop.close()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True