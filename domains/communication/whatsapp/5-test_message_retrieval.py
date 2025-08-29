# 5-test_message_retrieval.py

async def test_message_retrieval(zerg_state=None):
    """Test WhatsApp message retrieval for selected phone number"""
    print("Attempting to authenticate using WhatsApp connector")

    assert zerg_state, "this test requires valid zerg_state"

    whatsapp_access_token = zerg_state.get("whatsapp_access_token").get("value")
    whatsapp_phone_number_id = zerg_state.get("whatsapp_phone_number_id").get("value")
    whatsapp_business_account_id = zerg_state.get("whatsapp_business_account_id").get("value")
    whatsapp_api_base_url = zerg_state.get("whatsapp_api_base_url").get("value")

    from connectors.whatsapp.config import WhatsAppConnectorConfig
    from connectors.whatsapp.connector import WhatsAppConnector
    from connectors.whatsapp.tools import WhatsAppConnectorTools, GetWhatsAppMessagesInput
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
    phone_number_id = phone_number_selector.values[0] if phone_number_selector.values else None
    print(f"Selecting phone number id: {phone_number_id}")

    assert phone_number_id, f"failed to retrieve phone number id from phone number selector"

    # set up the target with phone number id
    target = WhatsAppTarget(phone_number_ids=[phone_number_id])
    assert isinstance(target, ConnectorTargetInterface), "WhatsAppTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_whatsapp_messages tool and execute it with phone number id
    get_whatsapp_messages_tool = next(tool for tool in tools if tool.name == "get_whatsapp_messages")
    whatsapp_messages_result = await get_whatsapp_messages_tool.execute(phone_number_id=phone_number_id)
    whatsapp_messages = whatsapp_messages_result.result

    print("Type of returned whatsapp_messages:", type(whatsapp_messages))
    print(f"len messages: {len(whatsapp_messages)} messages: {str(whatsapp_messages)[:200]}")

    # Verify that whatsapp_messages is a list
    assert isinstance(whatsapp_messages, list), "whatsapp_messages should be a list"
    assert len(whatsapp_messages) > 0, "whatsapp_messages should not be empty"
    
    # Limit the number of messages to check if there are many
    messages_to_check = whatsapp_messages[:5] if len(whatsapp_messages) > 5 else whatsapp_messages
    
    # Verify structure of each message object
    for message in messages_to_check:
        # Verify essential WhatsApp message fields
        assert "id" in message, "Each message should have an 'id' field"
        assert "from" in message, "Each message should have a 'from' field"
        assert "timestamp" in message, "Each message should have a 'timestamp' field"
        assert "type" in message, "Each message should have a 'type' field"
        
        # Verify common WhatsApp message fields
        message_type = message["type"]
        valid_types = ["text", "image", "document", "audio", "video", "location", "contacts", "template", "interactive"]
        assert message_type in valid_types, f"Message type should be one of {valid_types}, got {message_type}"
        
        # Verify message content based on type
        if message_type == "text":
            assert "text" in message, "Text message should have a 'text' field"
            assert "body" in message["text"], "Text message should have body content"
        
        # Check for additional optional fields
        optional_fields = ["context", "errors", "metadata", "referral", "button", "interactive"]
        present_optional = [field for field in optional_fields if field in message]
        
        print(f"Message {message['id']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first message for debugging
        if message == messages_to_check[0]:
            print(f"Example message structure: {message}")

    print(f"Successfully retrieved and validated {len(whatsapp_messages)} WhatsApp messages")

    return True