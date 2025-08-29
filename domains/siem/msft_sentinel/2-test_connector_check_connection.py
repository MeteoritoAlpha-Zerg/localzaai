# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing microsoft sentinel connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    azure_tenant_id = zerg_state.get("azure_tenant_id").get("value")
    client_id = zerg_state.get("client_id").get("value")
    client_secret = zerg_state.get("client_secret").get("value")
    subscription_id = zerg_state.get("subscription_id").get("value")
    resource_group = zerg_state.get("resource_group").get("value")

    from connectors.microsoft_sentinel.config import MicrosoftSentinelConnectorConfig
    from connectors.microsoft_sentinel.connector import MicrosoftSentinelConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = MicrosoftSentinelConnectorConfig(
        tenant_id=azure_tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        subscription_id=subscription_id,
        resource_group=resource_group,
    )
    assert isinstance(config, ConnectorConfig), "MicrosoftSentinelConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = MicrosoftSentinelConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MicrosoftSentinelConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True