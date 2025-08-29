# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing salesforce connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    salesforce_username = zerg_state.get("salesforce_username").get("value")
    salesforce_password = zerg_state.get("salesforce_password").get("value")
    salesforce_security_token = zerg_state.get("salesforce_security_token").get("value")
    salesforce_domain = zerg_state.get("salesforce_domain").get("value")

    from connectors.salesforce.config import SalesforceConnectorConfig
    from connectors.salesforce.connector import SalesforceConnector

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

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

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True