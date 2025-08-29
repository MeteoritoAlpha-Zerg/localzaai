# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to Google Chronicle"""
    print("Testing Google Chronicle connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    chronicle_service_account_path = zerg_state.get("chronicle_service_account_path").get("value")
    chronicle_customer_id = zerg_state.get("chronicle_customer_id").get("value")

    from connectors.chronicle.config import ChronicleConnectorConfig
    from connectors.chronicle.connector import ChronicleConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = ChronicleConnectorConfig(
        service_account_path=chronicle_service_account_path,
        customer_id=chronicle_customer_id,
    )
    assert isinstance(config, ConnectorConfig), "ChronicleConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ChronicleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ChronicleConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True