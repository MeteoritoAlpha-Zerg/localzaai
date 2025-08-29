# 6-test_dns_intelligence.py

async def test_dns_intelligence(zerg_state=None):
    """Test DomainTools DNS intelligence and domain relationship analysis"""
    print("Testing DomainTools DNS intelligence and domain relationship analysis")

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

    # get query target options to find available domain lists
    domaintools_query_target_options = await connector.get_query_target_options()
    assert isinstance(domaintools_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select domain list to target for DNS intelligence analysis
    domain_list_selector = None
    for selector in domaintools_query_target_options.selectors:
        if selector.type == 'domain_lists':  
            domain_list_selector = selector
            break

    assert domain_list_selector, "failed to retrieve domain list selector from query target options"

    assert isinstance(domain_list_selector.values, list), "domain_list_selector values must be a list"
    domain_list_id = domain_list_selector.values[0] if domain_list_selector.values else None
    print(f"Using domain list for DNS intelligence analysis: {domain_list_id}")

    assert domain_list_id, f"failed to retrieve domain list ID from domain list selector"

    # set up the target with domain list ID
    target = DomainToolsTarget(domain_lists=[domain_list_id])
    assert isinstance(target, ConnectorTargetInterface), "DomainToolsTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_dns_intelligence tool and execute DNS intelligence analysis
    get_dns_intel_tool = next(tool for tool in tools if tool.name == "get_dns_intelligence")
    
    # Execute DNS intelligence analysis
    dns_intel_result = await get_dns_intel_tool.execute(domain_list_id=domain_list_id)
    dns_intelligence = dns_intel_result.result

    print("Type of returned dns_intelligence:", type(dns_intelligence))
    print(f"DNS intelligence preview: {str(dns_intelligence)[:200]}")

    # Verify that dns_intelligence contains structured data
    assert dns_intelligence is not None, "dns_intelligence should not be None"
    
    # DNS intelligence could be a dictionary with metrics or a list of DNS items
    if isinstance(dns_intelligence, dict):
        # Check for common DNS intelligence fields
        expected_fields = ["total_domains", "dns_records", "infrastructure_analysis", "domain_relationships", "historical_data"]
        present_fields = [field for field in expected_fields if field in dns_intelligence]
        
        assert len(present_fields) > 0, f"DNS intelligence should contain at least one of these fields: {expected_fields}"
        print(f"DNS intelligence contains these fields: {', '.join(present_fields)}")
        
        # Verify numeric fields are actually numeric
        for field in present_fields:
            if "total" in field.lower() or "count" in field.lower():
                assert isinstance(dns_intelligence[field], (int, float)), f"Field {field} should be numeric"
        
        # Check for DNS records if present
        if "dns_records" in dns_intelligence:
            dns_records = dns_intelligence["dns_records"]
            assert isinstance(dns_records, (list, dict)), "dns_records should be structured data"
            
            if isinstance(dns_records, list) and len(dns_records) > 0:
                sample_record = dns_records[0]
                record_fields = ["type", "value", "domain", "ttl"]
                present_record_fields = [field for field in record_fields if field in sample_record]
                print(f"DNS records contain these fields: {', '.join(present_record_fields)}")
        
        # Check for domain relationships if present
        if "domain_relationships" in dns_intelligence:
            relationships = dns_intelligence["domain_relationships"]
            assert isinstance(relationships, (list, dict)), "domain_relationships should be structured data"
            
            if isinstance(relationships, list) and len(relationships) > 0:
                sample_relationship = relationships[0]
                rel_fields = ["related_domain", "relationship_type", "confidence_score"]
                present_rel_fields = [field for field in rel_fields if field in sample_relationship]
                print(f"Domain relationships contain these fields: {', '.join(present_rel_fields)}")
        
        # Log the full structure for debugging
        print(f"DNS intelligence structure: {dns_intelligence}")
        
    elif isinstance(dns_intelligence, list):
        assert len(dns_intelligence) > 0, "DNS intelligence list should not be empty"
        
        # Check structure of DNS intelligence items
        sample_item = dns_intelligence[0]
        assert isinstance(sample_item, dict), "DNS intelligence items should be dictionaries"
        
        # Look for common DNS intelligence fields
        item_fields = ["domain", "ip_addresses", "name_servers", "mx_records", "infrastructure_type"]
        present_item_fields = [field for field in item_fields if field in sample_item]
        
        print(f"DNS intelligence items contain these fields: {', '.join(present_item_fields)}")
        
        # Verify domain name if present
        if "domain" in sample_item:
            domain_name = sample_item["domain"]
            assert isinstance(domain_name, str), "Domain name should be a string"
            assert "." in domain_name, "Domain name should contain at least one dot"
        
        # Check for IP addresses if present
        if "ip_addresses" in sample_item:
            ip_addresses = sample_item["ip_addresses"]
            assert isinstance(ip_addresses, list), "IP addresses should be a list"
        
        # Check for infrastructure type if present
        if "infrastructure_type" in sample_item:
            infra_type = sample_item["infrastructure_type"]
            valid_infra_types = ["hosting", "cloud", "cdn", "residential", "datacenter", "unknown"]
            assert infra_type in valid_infra_types, f"Infrastructure type should be valid"
        
        print(f"Example DNS intelligence item: {sample_item}")
        
    else:
        # DNS intelligence could be in other formats, ensure it's meaningful
        assert str(dns_intelligence).strip() != "", "DNS intelligence should contain meaningful data"

    print(f"Successfully retrieved and validated DNS intelligence data")

    return True