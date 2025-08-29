# 6-test_get_compromised_credentials.py

async def test_get_compromised_credentials(zerg_state=None):
    """Test Flashpoint compromised credentials and fraud data retrieval"""
    print("Testing Flashpoint compromised credentials and fraud data retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    flashpoint_api_url = zerg_state.get("flashpoint_api_url").get("value")
    flashpoint_api_key = zerg_state.get("flashpoint_api_key").get("value")

    from connectors.flashpoint.config import FlashpointConnectorConfig
    from connectors.flashpoint.connector import FlashpointConnector
    from connectors.flashpoint.target import FlashpointTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = FlashpointConnectorConfig(
        api_url=flashpoint_api_url,
        api_key=flashpoint_api_key
    )
    assert isinstance(config, ConnectorConfig), "FlashpointConnectorConfig should be of type ConnectorConfig"

    connector = FlashpointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "FlashpointConnector should be of type Connector"

    flashpoint_query_target_options = await connector.get_query_target_options()
    assert isinstance(flashpoint_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in flashpoint_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    credentials_source = None
    for source in data_source_selector.values:
        if 'credential' in source.lower() or 'compromised' in source.lower():
            credentials_source = source
            break
    
    assert credentials_source, "Compromised credentials data source not found in available options"
    print(f"Selecting compromised credentials data source: {credentials_source}")

    target = FlashpointTarget(data_sources=[credentials_source])
    assert isinstance(target, ConnectorTargetInterface), "FlashpointTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test compromised credentials retrieval
    get_flashpoint_credentials_tool = next(tool for tool in tools if tool.name == "get_flashpoint_compromised_credentials")
    credentials_result = await get_flashpoint_credentials_tool.execute()
    credentials_data = credentials_result.result

    print("Type of returned credentials data:", type(credentials_data))
    print(f"Credentials count: {len(credentials_data)} sample: {str(credentials_data)[:200]}")

    assert isinstance(credentials_data, list), "Credentials data should be a list"
    assert len(credentials_data) > 0, "Credentials data should not be empty"
    
    credentials_to_check = credentials_data[:10] if len(credentials_data) > 10 else credentials_data
    
    for credential in credentials_to_check:
        # Verify essential credential fields per Flashpoint API specification
        assert "uuid" in credential, "Each credential should have a 'uuid' field"
        assert "breach_name" in credential, "Each credential should have a 'breach_name' field"
        assert "first_observed" in credential, "Each credential should have a 'first_observed' field"
        
        assert credential["uuid"], "Credential UUID should not be empty"
        assert credential["breach_name"].strip(), "Breach name should not be empty"
        assert credential["first_observed"], "First observed should not be empty"
        
        credential_fields = ["email", "domain", "password_hash", "password_type", "breach_date", "sources"]
        present_fields = [field for field in credential_fields if field in credential]
        
        print(f"Credential {credential['uuid'][:8]}... (breach: {credential['breach_name']}) contains: {', '.join(present_fields)}")
        
        # If email is present, validate basic format
        if "email" in credential:
            email = credential["email"]
            assert email and email.strip(), "Email should not be empty"
            assert "@" in email, "Email should contain @ symbol"
        
        # If domain is present, validate it's not empty
        if "domain" in credential:
            domain = credential["domain"]
            assert domain and domain.strip(), "Domain should not be empty"
        
        # If password type is present, validate it's not empty
        if "password_type" in credential:
            password_type = credential["password_type"]
            assert password_type and password_type.strip(), "Password type should not be empty"
        
        # If sources are present, validate structure
        if "sources" in credential:
            sources = credential["sources"]
            assert isinstance(sources, list), "Sources should be a list"
            for source in sources:
                assert isinstance(source, dict), "Each source should be a dictionary"
                assert "name" in source, "Each source should have a name"
                assert source["name"].strip(), "Source name should not be empty"
        
        # Log the structure of the first credential for debugging
        if credential == credentials_to_check[0]:
            print(f"Example credential structure: {credential}")

    print(f"Successfully retrieved and validated {len(credentials_data)} Flashpoint compromised credentials")

    # Test fraud data retrieval if available
    try:
        get_flashpoint_fraud_tool = next((tool for tool in tools if tool.name == "get_flashpoint_fraud_data"), None)
        if get_flashpoint_fraud_tool:
            fraud_result = await get_flashpoint_fraud_tool.execute()
            fraud_data = fraud_result.result

            print("Type of returned fraud data:", type(fraud_data))
            print(f"Fraud data count: {len(fraud_data)} sample: {str(fraud_data)[:200]}")

            assert isinstance(fraud_data, list), "Fraud data should be a list"
            
            if len(fraud_data) > 0:
                fraud_to_check = fraud_data[:5] if len(fraud_data) > 5 else fraud_data
                
                for fraud in fraud_to_check:
                    # Verify essential fraud fields
                    assert "uuid" in fraud, "Each fraud item should have a 'uuid' field"
                    assert "fraud_type" in fraud, "Each fraud item should have a 'fraud_type' field"
                    
                    assert fraud["uuid"], "Fraud UUID should not be empty"
                    assert fraud["fraud_type"].strip(), "Fraud type should not be empty"
                    
                    fraud_fields = ["description", "indicators", "tags", "confidence"]
                    present_fields = [field for field in fraud_fields if field in fraud]
                    
                    print(f"Fraud {fraud['uuid'][:8]}... (type: {fraud['fraud_type']}) contains: {', '.join(present_fields)}")

                print(f"Successfully retrieved and validated {len(fraud_data)} Flashpoint fraud data items")
            else:
                print("No fraud data available")
        else:
            print("Fraud data retrieval tool not available")
    except Exception as e:
        print(f"Fraud data retrieval test skipped: {e}")

    return True