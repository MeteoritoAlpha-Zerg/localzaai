# 3-test_query_target_options.py

async def test_phone_number_enumeration_options(zerg_state=None):
    """Test WhatsApp phone number enumeration by way of query target options"""
    print("Attempting to authenticate using WhatsApp connector")

    assert zerg_state, "this test requires valid zerg_state"

    whatsapp_access_token = zerg_state.get("whatsapp_access_token").get("value")
    whatsapp_phone_number_id = zerg_state.get("whatsapp_phone_number_id").get("value")
    whatsapp_business_account_id = zerg_state.get("whatsapp_business_account_id").get("value")
    whatsapp_api_base_url = zerg_state.get("whatsapp_api_base_url").get("value")

    from connectors.whatsapp.config import WhatsAppConnectorConfig
    from connectors.whatsapp.connector import WhatsAppConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = WhatsAppConnectorConfig(
        access_token=whatsapp_access_token,
        phone_number_id=whatsapp_phone_number_id,
        business_account_id=whatsapp_business_account_id,
        api_base_url=whatsapp_api_base_url,
    )
    assert isinstance(config, ConnectorConfig), "WhatsAppConnectorConfig should be of type ConnectorConfig"

    connector = WhatsAppConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "WhatsAppConnectorConfig should be of type ConnectorConfig"

    whatsapp_query_target_options = await connector.get_query_target_options()
    assert isinstance(whatsapp_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert whatsapp_query_target_options, "Failed to retrieve query target options"

    print(f"whatsapp query target option definitions: {whatsapp_query_target_options.definitions}")
    print(f"whatsapp query target option selectors: {whatsapp_query_target_options.selectors}")

    return True