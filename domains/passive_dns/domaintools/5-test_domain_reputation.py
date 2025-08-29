# 5-test_domain_reputation.py

async def test_domain_reputation(zerg_state=None):
    """Test DomainTools domain reputation score retrieval"""
    print("Testing DomainTools domain reputation score retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    domaintools_api_username = zerg_state.get("domaintools_api_username").get("value")
    domaintools_api_key = zerg_state.get("domaintools_api_key").get("value")
    domaintools_base_url = zerg_state.get("domaintools_base_url").get("value")

    from connectors.domaintools.config import DomainToolsConnectorConfig
    from connectors.domaintools.connector import DomainToolsConnector
    from connectors.domaintools.target import DomainToolsTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = DomainToolsConnectorConfig(
        api_username=domaintools_api_username,
        api_key=domaintools_api_key,
        base_url=domaintools_base_url
    )
    assert isinstance(config, ConnectorConfig), "DomainToolsConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = DomainToolsConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DomainToolsConnector should be of type Connector"

    # get query target options
    domaintools_query_target_options = await connector.get_query_target_options()
    assert isinstance(domaintools_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select domain list to target
    domain_list_selector = None
    for selector in domaintools_query_target_options.selectors:
        if selector.type == 'domain_lists':  
            domain_list_selector = selector
            break

    assert domain_list_selector, "failed to retrieve domain list selector from query target options"

    assert isinstance(domain_list_selector.values, list), "domain_list_selector values must be a list"
    domain_list_id = domain_list_selector.values[0] if domain_list_selector.values else None
    print(f"Selecting domain list ID: {domain_list_id}")

    assert domain_list_id, f"failed to retrieve domain list ID from domain list selector"

    # set up the target with domain list ID
    target = DomainToolsTarget(domain_lists=[domain_list_id])
    assert isinstance(target, ConnectorTargetInterface), "DomainToolsTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_domain_reputation tool and execute it with domain list ID
    get_domain_reputation_tool = next(tool for tool in tools if tool.name == "get_domain_reputation")
    reputation_result = await get_domain_reputation_tool.execute(domain_list_id=domain_list_id)
    reputation_data = reputation_result.result

    print("Type of returned reputation_data:", type(reputation_data))
    print(f"len reputation entries: {len(reputation_data)} entries: {str(reputation_data)[:200]}")

    # Verify that reputation_data is a list
    assert isinstance(reputation_data, list), "reputation_data should be a list"
    assert len(reputation_data) > 0, "reputation_data should not be empty"
    
    # Limit the number of reputation entries to check if there are many
    reputation_to_check = reputation_data[:5] if len(reputation_data) > 5 else reputation_data
    
    # Verify structure of each reputation object
    for reputation in reputation_to_check:
        # Verify reputation is a dictionary
        assert isinstance(reputation, dict), "Each reputation entry should be a dictionary"
        
        # Verify essential reputation fields
        assert "domain" in reputation, "Each reputation entry should have a 'domain' field"
        assert "risk_score" in reputation, "Each reputation entry should have a 'risk_score' field"
        
        # Verify domain name format
        domain_name = reputation["domain"]
        assert isinstance(domain_name, str), "Domain name should be a string"
        assert "." in domain_name, "Domain name should contain at least one dot"
        
        # Verify risk score is valid
        risk_score = reputation["risk_score"]
        assert isinstance(risk_score, (int, float)), "Risk score should be numeric"
        assert 0 <= risk_score <= 100, f"Risk score {risk_score} should be between 0 and 100"
        
        # Check for additional reputation fields
        reputation_fields = ["reputation", "threat_profile", "malware_risk", "phishing_risk", "spam_risk"]
        present_reputation_fields = [field for field in reputation_fields if field in reputation]
        
        print(f"Domain {domain_name} contains these reputation fields: {', '.join(present_reputation_fields)}")
        
        # Verify reputation level if present
        if "reputation" in reputation:
            valid_reputations = ["low", "medium", "high", "unknown"]
            assert reputation["reputation"] in valid_reputations, f"Reputation level should be valid"
        
        # Verify threat profile structure if present
        if "threat_profile" in reputation:
            threat_profile = reputation["threat_profile"]
            assert isinstance(threat_profile, dict), "Threat profile should be a dictionary"
            
            # Check for common threat profile fields
            threat_fields = ["malware", "phishing", "spam", "evidence"]
            present_threat_fields = [field for field in threat_fields if field in threat_profile]
            print(f"Threat profile contains: {', '.join(present_threat_fields)}")
        
        # Log the structure of the first reputation entry for debugging
        if reputation == reputation_to_check[0]:
            print(f"Example reputation structure: {reputation}")

    print(f"Successfully retrieved and validated {len(reputation_data)} domain reputation entries")

    return True