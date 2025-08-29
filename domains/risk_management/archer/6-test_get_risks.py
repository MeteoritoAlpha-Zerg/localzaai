# 6-test_get_risks.py

async def test_get_risks(zerg_state=None):
    """Test RSA Archer risk management data retrieval"""
    print("Testing RSA Archer risk management data retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    rsa_archer_api_url = zerg_state.get("rsa_archer_api_url").get("value")
    rsa_archer_username = zerg_state.get("rsa_archer_username").get("value")
    rsa_archer_password = zerg_state.get("rsa_archer_password").get("value")
    rsa_archer_instance_name = zerg_state.get("rsa_archer_instance_name").get("value")

    from connectors.rsa_archer.config import RSAArcherConnectorConfig
    from connectors.rsa_archer.connector import RSAArcherConnector
    from connectors.rsa_archer.target import RSAArcherTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = RSAArcherConnectorConfig(
        api_url=rsa_archer_api_url,
        username=rsa_archer_username,
        password=rsa_archer_password,
        instance_name=rsa_archer_instance_name
    )
    assert isinstance(config, ConnectorConfig), "RSAArcherConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = RSAArcherConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RSAArcherConnector should be of type Connector"

    # get query target options
    rsa_archer_query_target_options = await connector.get_query_target_options()
    assert isinstance(rsa_archer_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select risk-related application
    application_selector = None
    for selector in rsa_archer_query_target_options.selectors:
        if selector.type == 'applications':  
            application_selector = selector
            break

    assert application_selector, "failed to retrieve application selector from query target options"
    assert isinstance(application_selector.values, list), "application_selector values must be a list"
    
    # Find risk-related application
    risk_application = None
    for app in application_selector.values:
        if 'risk' in app.lower() or 'assessment' in app.lower():
            risk_application = app
            break
    
    # If no risk-specific app found, use the first available application
    if not risk_application:
        risk_application = application_selector.values[0]
    
    assert risk_application, "No applications available for risk retrieval"
    print(f"Selecting risk application: {risk_application}")

    # set up the target with risk application
    target = RSAArcherTarget(applications=[risk_application])
    assert isinstance(target, ConnectorTargetInterface), "RSAArcherTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_rsa_archer_risks tool and execute it
    get_rsa_archer_risks_tool = next(tool for tool in tools if tool.name == "get_rsa_archer_risks")
    risks_result = await get_rsa_archer_risks_tool.execute(application=risk_application)
    risks_data = risks_result.result

    print("Type of returned risks data:", type(risks_data))
    print(f"Risks count: {len(risks_data)} sample: {str(risks_data)[:200]}")

    # Verify that risks_data is a list
    assert isinstance(risks_data, list), "Risks data should be a list"
    assert len(risks_data) > 0, "Risks data should not be empty"
    
    # Limit the number of risks to check if there are many
    risks_to_check = risks_data[:5] if len(risks_data) > 5 else risks_data
    
    # Verify structure of each risk entry
    for risk in risks_to_check:
        # Verify essential risk fields per RSA Archer API specification
        assert "Id" in risk or "id" in risk, "Each risk should have an 'Id' or 'id' field"
        
        # Get the risk ID
        risk_id = risk.get("Id") or risk.get("id")
        assert risk_id, "Risk ID should not be empty"
        
        # Check for additional risk fields per RSA Archer specification
        risk_fields = ["Title", "Status", "RiskLevel", "Impact", "Likelihood", "RiskScore", "Description", "CreatedDate", "ModifiedDate", "Owner", "Fields"]
        present_fields = [field for field in risk_fields if field in risk]
        
        print(f"Risk {risk_id} contains: {', '.join(present_fields)}")
        
        # If Status is present, validate it's not empty
        if "Status" in risk:
            status = risk["Status"]
            assert status, "Risk status should not be empty"
        
        # If RiskLevel is present, validate it's not empty
        if "RiskLevel" in risk:
            risk_level = risk["RiskLevel"]
            assert risk_level, "Risk level should not be empty"
        
        # If Impact is present, validate it's not empty
        if "Impact" in risk:
            impact = risk["Impact"]
            assert impact, "Risk impact should not be empty"
        
        # If Likelihood is present, validate it's not empty
        if "Likelihood" in risk:
            likelihood = risk["Likelihood"]
            assert likelihood, "Risk likelihood should not be empty"
        
        # If RiskScore is present, validate it's numeric
        if "RiskScore" in risk:
            risk_score = risk["RiskScore"]
            if risk_score is not None:
                assert isinstance(risk_score, (int, float, str)), "Risk score should be numeric or string"
                if isinstance(risk_score, str):
                    assert risk_score.strip(), "Risk score string should not be empty"
        
        # If Title is present, validate it's not empty
        if "Title" in risk:
            title = risk["Title"]
            assert title and title.strip(), "Risk title should not be empty"
        
        # If Description is present, validate it's not empty
        if "Description" in risk:
            description = risk["Description"]
            assert description and description.strip(), "Risk description should not be empty"
        
        # If Fields are present, validate structure
        if "Fields" in risk:
            fields = risk["Fields"]
            assert isinstance(fields, (dict, list)), "Fields should be a dictionary or list"
        
        # If Owner is present, validate it's not empty
        if "Owner" in risk:
            owner = risk["Owner"]
            assert owner, "Risk owner should not be empty"
        
        # Log the structure of the first risk for debugging
        if risk == risks_to_check[0]:
            print(f"Example risk structure: {risk}")

    print(f"Successfully retrieved and validated {len(risks_data)} RSA Archer risks")

    return True