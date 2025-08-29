# 6-test_send_sms.py

from datetime import datetime

async def test_send_sms(zerg_state=None):
    """Test Twilio SMS sending from selected phone number"""
    print("Attempting to authenticate using Twilio connector")

    assert zerg_state, "this test requires valid zerg_state"

    twilio_account_sid = zerg_state.get("twilio_account_sid").get("value")
    twilio_auth_token = zerg_state.get("twilio_auth_token").get("value")
    twilio_api_base_url = zerg_state.get("twilio_api_base_url").get("value")

    from connectors.twilio.config import TwilioConnectorConfig
    from connectors.twilio.connector import TwilioConnector
    from connectors.twilio.tools import TwilioConnectorTools, SendTwilioSMSInput
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
    from_phone_number = phone_number_selector.values[0] if phone_number_selector.values else None
    print(f"Selecting from phone number: {from_phone_number}")

    assert from_phone_number, f"failed to retrieve phone number from phone number selector"

    # set up the target with phone number
    target = TwilioTarget(phone_numbers=[from_phone_number])
    assert isinstance(target, ConnectorTargetInterface), "TwilioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the send_twilio_sms tool and execute it with test message
    send_twilio_sms_tool = next(tool for tool in tools if tool.name == "send_twilio_sms")
    test_message = f"Test SMS from Twilio connector at {datetime.now().isoformat()}"
    test_to_number = from_phone_number  # Send to self for testing (if supported) or use a verified number
    
    send_result = await send_twilio_sms_tool.execute(
        from_phone_number=from_phone_number,
        to_phone_number=test_to_number,
        message=test_message
    )
    send_response = send_result.result

    print("Type of returned send_response:", type(send_response))
    print(f"Send response: {send_response}")

    # Verify that the SMS was sent successfully
    assert isinstance(send_response, dict), "send_response should be a dict"
    
    # Verify essential Twilio SMS response fields
    assert "sid" in send_response, "Response should have a 'sid' field"
    assert "account_sid" in send_response, "Response should have an 'account_sid' field"
    assert "from" in send_response, "Response should have a 'from' field"
    assert "to" in send_response, "Response should have a 'to' field"
    assert "status" in send_response, "Response should have a 'status' field"
    
    # Verify the response values match the request
    assert send_response["from"] == from_phone_number, f"Response 'from' should match requested from_phone_number"
    assert send_response["to"] == test_to_number, f"Response 'to' should match requested to_phone_number"
    
    # Verify status indicates successful queuing/sending
    valid_statuses = ["queued", "sent", "delivered", "accepted"]
    assert send_response["status"] in valid_statuses, f"Message status should be one of {valid_statuses}, got {send_response['status']}"
    
    # Check for additional response fields that indicate successful delivery
    expected_fields = ["body", "date_created", "direction", "price", "uri"]
    present_fields = [field for field in expected_fields if field in send_response]
    
    print(f"Response contains these additional fields: {', '.join(present_fields)}")
    
    # Verify message body if present
    if "body" in send_response:
        assert send_response["body"] == test_message, "Response body should match sent message"

    print(f"Successfully sent SMS from {from_phone_number} to {test_to_number}")
    print(f"Message SID: {send_response['sid']}")
    print(f"Status: {send_response['status']}")
    print(f"Response structure: {send_response}")

    return True