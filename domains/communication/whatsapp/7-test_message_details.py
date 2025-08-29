# 7-test_message_details.py

async def test_message_details(zerg_state=None):
    """Test WhatsApp message details retrieval including delivery status"""
    print("Attempting to authenticate using WhatsApp connector")

    assert zerg_state, "this test requires valid zerg_state"

    whatsapp_access_token = zerg_state.get("whatsapp_access_token").get("value")
    whatsapp_phone_number_id = zerg_state.get("whatsapp_phone_number_id").get("value")
    whatsapp_business_account_id = zerg_state.get("whatsapp_business_account_id").get("value")
    whatsapp_api_base_url = zerg_state.get("whatsapp_api_base_url").get("value")

    from connectors.whatsapp.config import WhatsAppConnectorConfig
    from connectors.whatsapp.connector import WhatsAppConnector
    from connectors.whatsapp.tools import WhatsAppConnectorTools, GetWhatsAppMessageDetailsInput
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

    # First get a list of messages to find one to retrieve details for
    get_whatsapp_messages_tool = next(tool for tool in tools if tool.name == "get_whatsapp_messages")
    whatsapp_messages_result = await get_whatsapp_messages_tool.execute(phone_number_id=phone_number_id)
    whatsapp_messages = whatsapp_messages_result.result

    assert isinstance(whatsapp_messages, list), "whatsapp_messages should be a list"
    assert len(whatsapp_messages) > 0, "whatsapp_messages should not be empty"

    # Use the first message for details retrieval test
    test_message = whatsapp_messages[0]
    message_id = test_message["id"]
    print(f"Testing details retrieval for message ID: {message_id}")

    # grab the get_whatsapp_message_details tool and execute it with message ID
    get_whatsapp_message_details_tool = next(tool for tool in tools if tool.name == "get_whatsapp_message_details")
    message_details_result = await get_whatsapp_message_details_tool.execute(message_id=message_id)
    message_details = message_details_result.result

    print("Type of returned message_details:", type(message_details))
    print(f"Message details keys: {list(message_details.keys()) if isinstance(message_details, dict) else 'Not a dict'}")

    # Verify that message_details is a dictionary
    assert isinstance(message_details, dict), "message_details should be a dict"
    
    # Verify essential message details fields
    assert "id" in message_details, "Message details should have an 'id' field"
    assert message_details["id"] == message_id, "Message details ID should match requested ID"
    
    assert "from" in message_details, "Message details should have a 'from' field"
    assert "timestamp" in message_details, "Message details should have a 'timestamp' field"
    assert "type" in message_details, "Message details should have a 'type' field"
    
    # Verify message type and content
    message_type = message_details["type"]
    valid_types = ["text", "image", "document", "audio", "video", "location", "contacts", "template", "interactive"]
    assert message_type in valid_types, f"Message type should be one of {valid_types}"
    
    # Verify type-specific content
    if message_type == "text":
        assert "text" in message_details, "Text message should have a 'text' field"
        assert "body" in message_details["text"], "Text message should have body content"
    
    # Check for delivery status information (if available)
    status_fields = ["status", "errors", "pricing"]
    present_status = [field for field in status_fields if field in message_details]
    
    print(f"Message contains these status fields: {', '.join(present_status)}")
    
    # Check for additional metadata fields
    metadata_fields = ["context", "referral", "metadata", "button", "interactive"]
    present_metadata = [field for field in metadata_fields if field in message_details]
    
    print(f"Message contains these metadata fields: {', '.join(present_metadata)}")
    
    # Check for conversation information
    conversation_fields = ["conversation", "billing"]
    present_conversation = [field for field in conversation_fields if field in message_details]
    
    print(f"Message contains these conversation fields: {', '.join(present_conversation)}")
    
    # Log a summary of the message details
    print(f"Example message details summary:")
    print(f"  - ID: {message_details['id']}")
    print(f"  - From: {message_details['from']}")
    print(f"  - Type: {message_details['type']}")
    print(f"  - Timestamp: {message_details['timestamp']}")
    
    if message_type == "text" and "text" in message_details:
        body = message_details["text"]["body"]
        print(f"  - Body preview: {body[:50]}..." if len(body) > 50 else f"  - Body: {body}")
    
    if "status" in message_details:
        print(f"  - Status: {message_details['status']}")
    
    if "errors" in message_details and message_details["errors"]:
        print(f"  - Errors: {message_details['errors']}")

    print(f"Successfully retrieved and validated message details for ID {message_id}")

    return True