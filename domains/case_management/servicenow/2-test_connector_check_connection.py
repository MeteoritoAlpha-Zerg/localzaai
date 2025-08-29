# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing servicenow connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    servicenow_instance_url = zerg_state.get("servicenow_instance_url").get("value")
    servicenow_client_id = zerg_state.get("servicenow_client_id").get("value")
    servicenow_client_secret = zerg_state.get("servicenow_client_secret").get("value")
    servicenow_username = zerg_state.get("servicenow_username").get("value")
    servicenow_password = zerg_state.get("servicenow_username").get("value")

    from connectors.servicenow.config import ServiceNowConnectorConfig
    from connectors.servicenow.connector import ServiceNowConnector
    from connectors.servicenow.target import ServiceNowTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = ServiceNowConnectorConfig(
        instance_url=servicenow_instance_url,
        client_id=servicenow_client_id,
        client_secret=servicenow_client_secret,
        servicenow_username=servicenow_username,
        servicenow_password=servicenow_password
    )
    assert isinstance(config, ConnectorConfig), "ServiceNowConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ServiceNowConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ServiceNowConnectorConfig should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True

