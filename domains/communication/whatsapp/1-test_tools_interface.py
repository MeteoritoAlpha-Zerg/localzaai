# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    whatsapp_access_token = zerg_state.get("whatsapp_access_token").get("value")
    whatsapp_phone_number_id = zerg_state.get("whatsapp_phone_number_id").get("value")
    whatsapp_business_account_id = zerg_state.get("whatsapp_business_account_id").get("value")
    whatsapp_api_base_url = zerg_state.get("whatsapp_api_base_url").get("value")

    from connectors.whatsapp.config import WhatsAppConnectorConfig
    from connectors.whatsapp.connector import WhatsAppConnector
    from connectors.whatsapp.target import WhatsAppTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
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

    target = WhatsAppTarget()
    assert isinstance(target, ConnectorTargetInterface), "WhatsAppTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True