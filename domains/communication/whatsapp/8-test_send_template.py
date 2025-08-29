# 8-test_send_template.py

async def test_send_template(zerg_state=None):
    """Test WhatsApp template message sending with parameters"""
    print("Attempting to authenticate using WhatsApp connector")

    assert zerg_state, "this test requires valid zerg_state"

    whatsapp_access_token = zerg_state.get("whatsapp_access_token").get("value")
    whatsapp_phone_number_id = zerg_state.get("whatsapp_phone_number_id").get("value")
    whatsapp_business_account_id = zerg_state.get("whatsapp_business_account_id").get("value")
    whatsapp_api_base_url = zerg_state.get("whatsapp_api_base_url").get("value")

    from connectors.whatsapp.config import WhatsAppConnectorConfig
    from connectors.whatsapp.connector import WhatsAppConnector
    from connectors.whatsapp.tools import WhatsAppConnectorTools, SendWhatsAppTemplateInput
    from connectors.whatsapp.target import WhatsAppTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = WhatsAppConnectorConfig(
        access_token=whatsapp_access_token,
        phone_number_id=whatsapp_phone_number_id,
        business_account_id=whatsapp_business_account_id,
        api_base_url=whatsapp_api_base_url
    )
    assert isinstance(config, ConnectorConfig), "WhatsAppConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = WhatsAppConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "WhatsAppConnectorConfig should be of type ConnectorConfig"

    # get query target options
    whatsapp_query_target_options = await connector.get_query_target_options()
    assert isinstance(whatsapp_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select phone number to target
    phone_number_selector = None
    for selector in whatsapp_query_target_options.selectors:
        if selector.type == 'phone_number_ids':  
            phone_number_selector = selector
            break

    assert phone_number_selector, "failed to retrieve phone number selector from query target options"

    assert isinstance(phone_number_selector.values, list), "phone_number_selector values must be a list"
    from_phone_number_id = phone_number_selector.values[0] if phone_number_selector.values else None
    print(f"Selecting from phone number id: {from_phone_number_id}")

    assert from_phone_number_id, f"failed to retrieve phone number id from phone number selector"

    # set up the target with phone number id
    target = WhatsAppTarget(phone_number_ids=[from_phone_number_id])
    assert isinstance(target, ConnectorTargetInterface), "WhatsAppTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the send_whatsapp_template tool and execute it with test template
    send_whatsapp_template_tool = next(tool for tool in tools if tool.name == "send_whatsapp_template")
    
    # Use a common template name - "hello_world" is typically available for testing
    template_name = "hello_world"
    test_to_number = "+1234567890"  # Use a test number or verified contact
    language_code = "en_US"
    
    # Template parameters (if the template requires them)
    template_parameters = []  # hello_world template typically has no parameters
    
    send_result = await send_whatsapp_template_tool.execute(
        phone_number_id=from_phone_number_id,
        to=test_to_number,
        template_name=template_name,
        language_code=language_code,
        parameters=template_parameters
    )
    send_response = send_result.result

    print("Type of returned send_response:", type(send_response))
    print(f"Send response: {send_response}")

    # Verify that the WhatsApp template message was sent successfully
    assert isinstance(send_response, dict), "send_response should be a dict"
    
    # Verify essential WhatsApp template response fields
    assert "messages" in send_response, "Response should have a 'messages' field"
    assert isinstance(send_response["messages"], list), "messages should be a list"
    assert len(send_response["messages"]) > 0, "messages should not be empty"
    
    message_response = send_response["messages"][0]
    assert "id" in message_response, "Message response should have an 'id' field"
    
    # Check for additional response fields that indicate successful delivery
    expected_fields = ["messaging_product", "contacts"]
    for field in expected_fields:
        if field in send_response:
            print(f"Response contains field '{field}': {send_response[field]}")
    
    # Verify messaging product
    if "messaging_product" in send_response:
        assert send_response["messaging_product"] == "whatsapp", "messaging_product should be 'whatsapp'"
    
    # Verify contacts information if present
    if "contacts" in send_response:
        contacts = send_response["contacts"]
        assert isinstance(contacts, list), "contacts should be a list"
        if len(contacts) > 0:
            contact = contacts[0]
            assert "input" in contact, "Contact should have an 'input' field"
            assert contact["input"] == test_to_number, "Contact input should match recipient number"
            
            # Check for WhatsApp ID if present
            if "wa_id" in contact:
                print(f"Recipient WhatsApp ID: {contact['wa_id']}")

    print(f"Successfully sent WhatsApp template message from phone number ID {from_phone_number_id} to {test_to_number}")
    print(f"Template: {template_name} ({language_code})")
    print(f"Message ID: {message_response['id']}")
    print(f"Response structure: {send_response}")

    return True