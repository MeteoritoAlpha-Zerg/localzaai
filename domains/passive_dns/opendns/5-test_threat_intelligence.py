# 5-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test OpenDNS threat intelligence and domain categorization retrieval"""
    print("Attempting to retrieve threat intelligence using OpenDNS connector")

    assert zerg_state, "this test requires valid zerg_state"

    opendns_api_key = zerg_state.get("opendns_api_key").get("value")
    opendns_api_secret = zerg_state.get("opendns_api_secret").get("value")
    opendns_organization_id = zerg_state.get("opendns_organization_id").get("value")

    from connectors.opendns.config import OpenDNSConnectorConfig
    from connectors.opendns.connector import OpenDNSConnector
    from connectors.opendns.tools import OpenDNSConnectorTools, GetDomainCategorizationInput
    from connectors.opendns.target import OpenDNSTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = OpenDNSConnectorConfig(
        api_key=opendns_api_key,
        api_secret=opendns_api_secret,
        organization_id=opendns_organization_id
    )
    assert isinstance(config, ConnectorConfig), "OpenDNSConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = OpenDNSConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "OpenDNSConnector should be of type Connector"

    # get query target options
    opendns_query_target_options = await connector.get_query_target_options()
    assert isinstance(opendns_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select organizations to target
    org_selector = None
    for selector in opendns_query_target_options.selectors:
        if selector.type == 'organization_ids':  
            org_selector = selector
            break

    assert org_selector, "failed to retrieve organization selector from query target options"

    assert isinstance(org_selector.values, list), "org_selector values must be a list"
    org_id = org_selector.values[0] if org_selector.values else None
    print(f"Selecting organization ID: {org_id}")

    assert org_id, f"failed to retrieve organization ID from organization selector"

    # set up the target with organization ID
    target = OpenDNSTarget(organization_ids=[org_id])
    assert isinstance(target, ConnectorTargetInterface), "OpenDNSTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_domain_categorization tool and execute it with test domains
    get_domain_categorization_tool = next(tool for tool in tools if tool.name == "get_domain_categorization")
    test_domains = ["google.com", "facebook.com", "malware-test.example.com"]
    domain_categorization_result = await get_domain_categorization_tool.execute(domains=test_domains)
    domain_categorization = domain_categorization_result.result

    print("Type of returned domain_categorization:", type(domain_categorization))
    print(f"Domain categorization data: {str(domain_categorization)[:200]}")

    # Verify that domain_categorization is a dictionary or list
    assert isinstance(domain_categorization, (dict, list)), "domain_categorization should be a dictionary or list"
    
    if isinstance(domain_categorization, dict):
        # If it's a dictionary, check each domain
        for domain in test_domains:
            if domain in domain_categorization:
                domain_info = domain_categorization[domain]
                assert "categories" in domain_info, f"Domain {domain} should have 'categories' field"
                assert "security_categories" in domain_info, f"Domain {domain} should have 'security_categories' field"
                
                print(f"Domain {domain} categorization: {domain_info.get('categories', [])}")
    else:
        # If it's a list, verify each entry
        for entry in domain_categorization:
            assert "domain" in entry, "Each categorization entry should have a 'domain' field"
            assert "categories" in entry, "Each categorization entry should have a 'categories' field"
    
    # Test threat intelligence lookup if available
    if "get_threat_intelligence" in [tool.name for tool in tools]:
        get_threat_intel_tool = next(tool for tool in tools if tool.name == "get_threat_intelligence")
        threat_intel_result = await get_threat_intel_tool.execute(
            domain="malware-test.example.com",
            include_co_occurrences=True
        )
        threat_intel = threat_intel_result.result
        
        print("Type of returned threat_intel:", type(threat_intel))
        
        if threat_intel:
            assert isinstance(threat_intel, dict), "threat_intel should be a dictionary"
            
            # Check for threat intelligence fields
            optional_fields = ["threat_types", "security_categories", "co_occurrences", "risk_score"]
            present_fields = [field for field in optional_fields if field in threat_intel]
            
            print(f"Threat intelligence contains these fields: {', '.join(present_fields)}")
    
    # Test domain security info if available
    if "get_domain_security_info" in [tool.name for tool in tools]:
        get_security_info_tool = next(tool for tool in tools if tool.name == "get_domain_security_info")
        security_info_result = await get_security_info_tool.execute(domain="google.com")
        security_info = security_info_result.result
        
        if security_info:
            assert isinstance(security_info, dict), "security_info should be a dictionary"
            
            # Verify security information fields
            security_fields = ["found", "dga_score", "perplexity", "entropy"]
            present_security_fields = [field for field in security_fields if field in security_info]
            
            print(f"Domain security info contains these fields: {', '.join(present_security_fields)}")
    
    # Log the structure for debugging
    print(f"Example domain categorization structure: {domain_categorization}")

    print(f"Successfully retrieved domain categorization data")

    return True