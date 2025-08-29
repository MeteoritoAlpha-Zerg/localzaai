# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing whatsapp connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    whatsapp_access_token = zerg_state.get("whatsapp_access_token").get("value")
    whatsapp_phone_number_id = zerg_state.get("whatsapp_phone_number_id").get("value")
    whatsapp_business_account_id = zerg_state.get("whatsapp_business_account_id").get("value")
    whatsapp_api_base_url = zerg_state.get("whatsapp_api_base_url").get("value")

    from connectors.whatsapp.config import WhatsAppConnectorConfig
    from connectors.whatsapp.connector import WhatsAppConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = WhatsAppConnectorConfig(
        access_token=whatsapp_access_token,
        phone_number_id=whatsapp_phone_number_id,
        business_account_id=whatsapp_business_account_id,
        api_base_url=whatsapp_api_base_url,
    )
    assert isinstance(config, ConnectorConfig), "WhatsAppConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = WhatsAppConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "WhatsAppConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True