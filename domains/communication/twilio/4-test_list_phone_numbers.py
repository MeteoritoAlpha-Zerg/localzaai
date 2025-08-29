# 4-test_list_phone_numbers.py

async def test_list_phone_numbers(zerg_state=None):
    """Test Twilio phone number enumeration by way of query target options"""
    print("Attempting to authenticate using Twilio connector")

    assert zerg_state, "this test requires valid zerg_state"

    twilio_account_sid = zerg_state.get("twilio_account_sid").get("value")
    twilio_auth_token = zerg_state.get("twilio_auth_token").get("value")
    twilio_api_base_url = zerg_state.get("twilio_api_base_url").get("value")

    from connectors.twilio.config import TwilioConnectorConfig
    from connectors.twilio.connector import TwilioConnector
    from connectors.twilio.tools import TwilioConnectorTools
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

    # select phone numbers to target
    phone_number_selector = None
    for selector in twilio_query_target_options.selectors:
        if selector.type == 'phone_numbers':  
            phone_number_selector = selector
            break

    assert phone_number_selector, "failed to retrieve phone number selector from query target options"

    # grab the first two phone numbers 
    num_phone_numbers = 2
    assert isinstance(phone_number_selector.values, list), "phone_number_selector values must be a list"
    phone_numbers = phone_number_selector.values[:num_phone_numbers] if phone_number_selector.values else None
    print(f"Selecting phone numbers: {phone_numbers}")

    assert phone_numbers, f"failed to retrieve {num_phone_numbers} phone numbers from phone number selector"

    # set up the target with phone numbers
    target = TwilioTarget(phone_numbers=phone_numbers)
    assert isinstance(target, ConnectorTargetInterface), "TwilioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_twilio_phone_numbers tool
    twilio_get_phone_numbers_tool = next(tool for tool in tools if tool.name == "get_twilio_phone_numbers")
    twilio_phone_numbers_result = await twilio_get_phone_numbers_tool.execute()
    twilio_phone_numbers = twilio_phone_numbers_result.result

    print("Type of returned twilio_phone_numbers:", type(twilio_phone_numbers))
    print(f"len phone numbers: {len(twilio_phone_numbers)} phone numbers: {str(twilio_phone_numbers)[:200]}")

    # ensure that twilio_phone_numbers are a list of objects with the phone_number being the phone number
    # and the object having the phone number capabilities and other relevant information from the twilio specification
    # as may be descriptive
    # Verify that twilio_phone_numbers is a list
    assert isinstance(twilio_phone_numbers, list), "twilio_phone_numbers should be a list"
    assert len(twilio_phone_numbers) > 0, "twilio_phone_numbers should not be empty"
    assert len(twilio_phone_numbers) == num_phone_numbers, f"twilio_phone_numbers should have {num_phone_numbers} entries"
    
    # Verify structure of each phone number object
    for phone_number in twilio_phone_numbers:
        assert "phone_number" in phone_number, "Each phone number should have a 'phone_number' field"
        assert phone_number["phone_number"] in phone_numbers, f"Phone number {phone_number['phone_number']} is not in the requested phone_numbers"
        
        # Verify essential Twilio phone number fields
        # These are common fields in Twilio phone numbers based on Twilio API specification
        assert "sid" in phone_number, "Each phone number should have a 'sid' field"
        assert "account_sid" in phone_number, "Each phone number should have an 'account_sid' field"
        assert "friendly_name" in phone_number, "Each phone number should have a 'friendly_name' field"
        
        # Check for additional descriptive fields (optional in some Twilio instances)
        descriptive_fields = ["capabilities", "status", "date_created", "date_updated", "sms_url", "voice_url"]
        present_fields = [field for field in descriptive_fields if field in phone_number]
        
        print(f"Phone number {phone_number['phone_number']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if phone_number == twilio_phone_numbers[0]:
            print(f"Example phone number structure: {phone_number}")

    print(f"Successfully retrieved and validated {len(twilio_phone_numbers)} Twilio phone numbers")

    return True