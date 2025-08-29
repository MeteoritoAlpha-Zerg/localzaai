# 7-test_message_details.py

async def test_message_details(zerg_state=None):
    """Test Twilio message details retrieval including delivery status"""
    print("Attempting to authenticate using Twilio connector")

    assert zerg_state, "this test requires valid zerg_state"

    twilio_account_sid = zerg_state.get("twilio_account_sid").get("value")
    twilio_auth_token = zerg_state.get("twilio_auth_token").get("value")
    twilio_api_base_url = zerg_state.get("twilio_api_base_url").get("value")

    from connectors.twilio.config import TwilioConnectorConfig
    from connectors.twilio.connector import TwilioConnector
    from connectors.twilio.tools import TwilioConnectorTools, GetTwilioMessageDetailsInput
    from connectors.twilio.target import TwilioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = TwilioConnectorConfig(
        account_sid=twilio_account_sid,
        auth_token=twilio_auth_token,
        api_base_url=twilio_api_base_url
    )
    assert isinstance(config, ConnectorConfig), "TwilioConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = TwilioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TwilioConnectorConfig should be of type ConnectorConfig"

    # get query target options
    twilio_query_target_options = await connector.get_query_target_options()
    assert isinstance(twilio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select phone number to target
    phone_number_selector = None
    for selector in twilio_query_target_options.selectors:
        if selector.type == 'phone_numbers':  
            phone_number_selector = selector
            break

    assert phone_number_selector, "failed to retrieve phone number selector from query target options"

    assert isinstance(phone_number_selector.values, list), "phone_number_selector values must be a list"
    phone_number = phone_number_selector.values[0] if phone_number_selector.values else None
    print(f"Selecting phone number: {phone_number}")

    assert phone_number, f"failed to retrieve phone number from phone number selector"

    # set up the target with phone number
    target = TwilioTarget(phone_numbers=[phone_number])
    assert isinstance(target, ConnectorTargetInterface), "TwilioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # First get a list of messages to find one to retrieve details for
    get_twilio_messages_tool = next(tool for tool in tools if tool.name == "get_twilio_messages")
    twilio_messages_result = await get_twilio_messages_tool.execute(phone_number=phone_number)
    twilio_messages = twilio_messages_result.result

    assert isinstance(twilio_messages, list), "twilio_messages should be a list"
    assert len(twilio_messages) > 0, "twilio_messages should not be empty"

    # Use the first message for details retrieval test
    test_message = twilio_messages[0]
    message_sid = test_message["sid"]
    print(f"Testing details retrieval for message SID: {message_sid}")

    # grab the get_twilio_message_details tool and execute it with message SID
    get_twilio_message_details_tool = next(tool for tool in tools if tool.name == "get_twilio_message_details")
    message_details_result = await get_twilio_message_details_tool.execute(message_sid=message_sid)
    message_details = message_details_result.result

    print("Type of returned message_details:", type(message_details))
    print(f"Message details keys: {list(message_details.keys()) if isinstance(message_details, dict) else 'Not a dict'}")

    # Verify that message_details is a dictionary
    assert isinstance(message_details, dict), "message_details should be a dict"
    
    # Verify essential message details fields
    assert "sid" in message_details, "Message details should have a 'sid' field"
    assert message_details["sid"] == message_sid, "Message details SID should match requested SID"
    
    assert "account_sid" in message_details, "Message details should have an 'account_sid' field"
    assert "from" in message_details, "Message details should have a 'from' field"
    assert "to" in message_details, "Message details should have a 'to' field"
    assert "body" in message_details, "Message details should have a 'body' field"
    assert "status" in message_details, "Message details should have a 'status' field"
    assert "direction" in message_details, "Message details should have a 'direction' field"
    
    # Verify timestamp fields
    timestamp_fields = ["date_created", "date_sent", "date_updated"]
    present_timestamps = [field for field in timestamp_fields if field in message_details]
    assert len(present_timestamps) > 0, "Message should have at least one timestamp field"
    
    print(f"Message contains these timestamp fields: {', '.join(present_timestamps)}")
    
    # Verify status-related information
    valid_statuses = ["queued", "sent", "delivered", "failed", "undelivered", "received"]
    assert message_details["status"] in valid_statuses, f"Message status should be one of {valid_statuses}"
    
    # Check for delivery and error information
    delivery_fields = ["error_code", "error_message", "price", "price_unit"]
    present_delivery = [field for field in delivery_fields if field in message_details]
    
    print(f"Message contains these delivery fields: {', '.join(present_delivery)}")
    
    # Check for additional metadata fields
    metadata_fields = ["num_segments", "num_media", "uri", "subresource_uris"]
    present_metadata = [field for field in metadata_fields if field in message_details]
    
    print(f"Message contains these metadata fields: {', '.join(present_metadata)}")
    
    # Verify the message is associated with the target phone number
    assert message_details["from"] == phone_number or message_details["to"] == phone_number, f"Message is not associated with target phone number {phone_number}"
    
    # Log a summary of the message details
    print(f"Example message details summary:")
    print(f"  - SID: {message_details['sid']}")
    print(f"  - From: {message_details['from']}")
    print(f"  - To: {message_details['to']}")
    print(f"  - Status: {message_details['status']}")
    print(f"  - Direction: {message_details['direction']}")
    print(f"  - Body preview: {message_details['body'][:50]}..." if len(message_details['body']) > 50 else f"  - Body: {message_details['body']}")
    
    if "error_code" in message_details and message_details["error_code"]:
        print(f"  - Error: {message_details['error_code']} - {message_details.get('error_message', 'N/A')}")
    
    if "price" in message_details and message_details["price"]:
        print(f"  - Price: {message_details['price']} {message_details.get('price_unit', '')}")

    print(f"Successfully retrieved and validated message details for SID {message_sid}")

    return True