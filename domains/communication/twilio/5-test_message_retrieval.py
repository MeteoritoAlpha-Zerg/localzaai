# 5-test_message_retrieval.py

async def test_message_retrieval(zerg_state=None):
    """Test Twilio message retrieval for selected phone number"""
    print("Attempting to authenticate using Twilio connector")

    assert zerg_state, "this test requires valid zerg_state"

    twilio_account_sid = zerg_state.get("twilio_account_sid").get("value")
    twilio_auth_token = zerg_state.get("twilio_auth_token").get("value")
    twilio_api_base_url = zerg_state.get("twilio_api_base_url").get("value")

    from connectors.twilio.config import TwilioConnectorConfig
    from connectors.twilio.connector import TwilioConnector
    from connectors.twilio.tools import TwilioConnectorTools, GetTwilioMessagesInput
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

    # grab the get_twilio_messages tool and execute it with phone number
    get_twilio_messages_tool = next(tool for tool in tools if tool.name == "get_twilio_messages")
    twilio_messages_result = await get_twilio_messages_tool.execute(phone_number=phone_number)
    twilio_messages = twilio_messages_result.result

    print("Type of returned twilio_messages:", type(twilio_messages))
    print(f"len messages: {len(twilio_messages)} messages: {str(twilio_messages)[:200]}")

    # Verify that twilio_messages is a list
    assert isinstance(twilio_messages, list), "twilio_messages should be a list"
    assert len(twilio_messages) > 0, "twilio_messages should not be empty"
    
    # Limit the number of messages to check if there are many
    messages_to_check = twilio_messages[:5] if len(twilio_messages) > 5 else twilio_messages
    
    # Verify structure of each message object
    for message in messages_to_check:
        # Verify essential Twilio message fields
        assert "sid" in message, "Each message should have a 'sid' field"
        assert "account_sid" in message, "Each message should have an 'account_sid' field"
        assert "from" in message, "Each message should have a 'from' field"
        assert "to" in message, "Each message should have a 'to' field"
        assert "body" in message, "Each message should have a 'body' field"
        
        # Check if message is associated with the requested phone number
        assert message["from"] == phone_number or message["to"] == phone_number, f"Message {message['sid']} is not associated with the requested phone_number"
        
        # Verify common Twilio message fields
        assert "status" in message, "Each message should have a 'status' field"
        assert "direction" in message, "Each message should have a 'direction' field"
        assert "date_created" in message, "Each message should have a 'date_created' field"
        
        # Check for additional optional fields
        optional_fields = ["date_sent", "date_updated", "error_code", "error_message", "price", "price_unit", "uri", "num_segments"]
        present_optional = [field for field in optional_fields if field in message]
        
        print(f"Message {message['sid']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first message for debugging
        if message == messages_to_check[0]:
            print(f"Example message structure: {message}")

    print(f"Successfully retrieved and validated {len(twilio_messages)} Twilio messages")

    return True