# 4-test_list_phone_numbers.py

async def test_list_phone_numbers(zerg_state=None):
    """Test WhatsApp phone number enumeration by way of query target options"""
    print("Attempting to authenticate using WhatsApp connector")

    assert zerg_state, "this test requires valid zerg_state"

    whatsapp_access_token = zerg_state.get("whatsapp_access_token").get("value")
    whatsapp_phone_number_id = zerg_state.get("whatsapp_phone_number_id").get("value")
    whatsapp_business_account_id = zerg_state.get("whatsapp_business_account_id").get("value")
    whatsapp_api_base_url = zerg_state.get("whatsapp_api_base_url").get("value")

    from connectors.whatsapp.config import WhatsAppConnectorConfig
    from connectors.whatsapp.connector import WhatsAppConnector
    from connectors.whatsapp.tools import WhatsAppConnectorTools
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

    # select phone numbers to target
    phone_number_selector = None
    for selector in whatsapp_query_target_options.selectors:
        if selector.type == 'phone_number_ids':  
            phone_number_selector = selector
            break

    assert phone_number_selector, "failed to retrieve phone number selector from query target options"

    # grab the first two phone numbers 
    num_phone_numbers = 2
    assert isinstance(phone_number_selector.values, list), "phone_number_selector values must be a list"
    phone_number_ids = phone_number_selector.values[:num_phone_numbers] if phone_number_selector.values else None
    print(f"Selecting phone number ids: {phone_number_ids}")

    assert phone_number_ids, f"failed to retrieve {num_phone_numbers} phone number ids from phone number selector"

    # set up the target with phone number ids
    target = WhatsAppTarget(phone_number_ids=phone_number_ids)
    assert isinstance(target, ConnectorTargetInterface), "WhatsAppTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_whatsapp_phone_numbers tool
    whatsapp_get_phone_numbers_tool = next(tool for tool in tools if tool.name == "get_whatsapp_phone_numbers")
    whatsapp_phone_numbers_result = await whatsapp_get_phone_numbers_tool.execute()
    whatsapp_phone_numbers = whatsapp_phone_numbers_result.result

    print("Type of returned whatsapp_phone_numbers:", type(whatsapp_phone_numbers))
    print(f"len phone numbers: {len(whatsapp_phone_numbers)} phone numbers: {str(whatsapp_phone_numbers)[:200]}")

    # ensure that whatsapp_phone_numbers are a list of objects with the id being the phone number id
    # and the object having the phone number status and other relevant information from the whatsapp specification
    # as may be descriptive
    # Verify that whatsapp_phone_numbers is a list
    assert isinstance(whatsapp_phone_numbers, list), "whatsapp_phone_numbers should be a list"
    assert len(whatsapp_phone_numbers) > 0, "whatsapp_phone_numbers should not be empty"
    assert len(whatsapp_phone_numbers) == num_phone_numbers, f"whatsapp_phone_numbers should have {num_phone_numbers} entries"
    
    # Verify structure of each phone number object
    for phone_number in whatsapp_phone_numbers:
        assert "id" in phone_number, "Each phone number should have an 'id' field"
        assert phone_number["id"] in phone_number_ids, f"Phone number id {phone_number['id']} is not in the requested phone_number_ids"
        
        # Verify essential WhatsApp phone number fields
        # These are common fields in WhatsApp phone numbers based on WhatsApp Business API specification
        assert "display_phone_number" in phone_number, "Each phone number should have a 'display_phone_number' field"
        assert "verified_name" in phone_number, "Each phone number should have a 'verified_name' field"
        assert "status" in phone_number, "Each phone number should have a 'status' field"
        
        # Check for additional descriptive fields (optional in some WhatsApp instances)
        descriptive_fields = ["quality_rating", "platform_type", "throughput", "name_status", "certificate", "code_verification_status"]
        present_fields = [field for field in descriptive_fields if field in phone_number]
        
        print(f"Phone number {phone_number['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if phone_number == whatsapp_phone_numbers[0]:
            print(f"Example phone number structure: {phone_number}")

    print(f"Successfully retrieved and validated {len(whatsapp_phone_numbers)} WhatsApp phone numbers")

    return True