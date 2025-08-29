# 3-test_query_target_options.py

async def test_project_enumeration_options(zerg_state=None):
    """Test Salesforce project enumeration by way of query target options"""
    print("Attempting to authenticate using Salesforce connector")

    assert zerg_state, "this test requires valid zerg_state"

    salesforce_username = zerg_state.get("salesforce_username").get("value")
    salesforce_password = zerg_state.get("salesforce_password").get("value")
    salesforce_security_token = zerg_state.get("salesforce_security_token").get("value")
    salesforce_domain = zerg_state.get("salesforce_domain").get("value")

    from connectors.salesforce.config import SalesforceConnectorConfig
    from connectors.salesforce.connector import SalesforceConnector

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SalesforceConnectorConfig(
        username=salesforce_username,
        password=salesforce_password,
        security_token=salesforce_security_token,
        domain=salesforce_domain
    )
    assert isinstance(config, ConnectorConfig), "SalesforceConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SalesforceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SalesforceConnector should be of type Connector"

    query_target_options = await connector.get_query_target_options()
    assert isinstance(query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert query_target_options, "Failed to retrieve query target options"

    print(f"salesforce query target option definitions: {query_target_options.definitions}")
    print(f"salesforce query target option selectors: {query_target_options.selectors}")

    return True