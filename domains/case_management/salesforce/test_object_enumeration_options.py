async def test_object_enumeration_options(zerg_state=None):
    """Test Salesforce object enumeration by way of query target options"""
    print("Attempting to authenticate using Salesforce connector")

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

    connector_target = SalesforceTarget(config=config)

    salesforce_query_target_options = await connector.get_query_target_options()

    assert salesforce_query_target_options, "Failed to retrieve query target options"

    # TODO: what else do we want to do here
    print(f"salesforce query target option definitions: {salesforce_query_target_options.definitions}")
    print(f"salesforce query target option selectors: {salesforce_query_target_options.selectors}")

    return True