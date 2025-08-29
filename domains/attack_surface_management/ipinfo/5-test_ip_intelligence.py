# 5-test_ip_intelligence.py

async def test_ip_intelligence(zerg_state=None):
    """Test IPInfo IP intelligence and threat analysis retrieval by way of connector tools"""
    print("Attempting to authenticate using IPInfo connector")

    assert zerg_state, "this test requires valid zerg_state"

    ipinfo_api_token = zerg_state.get("ipinfo_api_token").get("value")
    ipinfo_base_url = zerg_state.get("ipinfo_base_url").get("value")
    ipinfo_api_version = zerg_state.get("ipinfo_api_version").get("value")

    from connectors.ipinfo.config import IPInfoConnectorConfig
    from connectors.ipinfo.connector import IPInfoConnector
    from connectors.ipinfo.tools import IPInfoConnectorTools, GetIPIntelligenceInput
    from connectors.ipinfo.target import IPInfoTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = IPInfoConnectorConfig(
        api_token=ipinfo_api_token,
        base_url=ipinfo_base_url,
        api_version=ipinfo_api_version
    )
    assert isinstance(config, ConnectorConfig), "IPInfoConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = IPInfoConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "IPInfoConnector should be of type Connector"

    # get query target options
    ipinfo_query_target_options = await connector.get_query_target_options()
    assert isinstance(ipinfo_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select data services to target
    data_service_selector = None
    for selector in ipinfo_query_target_options.selectors:
        if selector.type == 'data_services':  
            data_service_selector = selector
            break

    assert data_service_selector, "failed to retrieve data service selector from query target options"

    # grab intelligence-related data services
    assert isinstance(data_service_selector.values, list), "data_service_selector values must be a list"
    
    # Look for intelligence and privacy services
    intelligence_services = []
    desired_services = ["privacy", "abuse", "hosting", "domains"]
    for service in desired_services:
        if service in data_service_selector.values:
            intelligence_services.append(service)
    
    # Use at least one service for intelligence analysis
    if not intelligence_services:
        intelligence_services = ["geolocation"]  # Fallback to basic service
    
    print(f"Selecting intelligence services: {intelligence_services}")

    # set up the target with intelligence services
    target = IPInfoTarget(data_services=intelligence_services)
    assert isinstance(target, ConnectorTargetInterface), "IPInfoTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_ipinfo_ip_intelligence tool and execute it
    get_ip_intelligence_tool = next(tool for tool in tools if tool.name == "get_ipinfo_ip_intelligence")
    
    # Test with a mix of IP addresses for comprehensive intelligence analysis
    test_ip_addresses = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]  # Known public DNS services
    
    for test_ip in test_ip_addresses:
        print(f"Testing IP intelligence for IP: {test_ip}")
        
        # Get IP intelligence with privacy and hosting analysis
        intelligence_result = await get_ip_intelligence_tool.execute(
            ip_address=test_ip, 
            include_privacy=True, 
            include_abuse=True,
            include_hosting=True
        )
        ip_intelligence_data = intelligence_result.result

        print("Type of returned ip_intelligence_data:", type(ip_intelligence_data))
        print(f"IP intelligence data for {test_ip}: {str(ip_intelligence_data)[:200]}")

        # Verify that ip_intelligence_data is a dictionary
        assert isinstance(ip_intelligence_data, dict), "ip_intelligence_data should be a dictionary"
        assert len(ip_intelligence_data) > 0, "ip_intelligence_data should not be empty"
        
        # Verify essential IPInfo IP intelligence fields
        assert "ip" in ip_intelligence_data, "IP intelligence data should have an 'ip' field"
        assert ip_intelligence_data["ip"] == test_ip, f"Returned IP {ip_intelligence_data['ip']} should match requested IP {test_ip}"
        
        # Check for privacy detection and analysis
        privacy_fields = ["privacy"]
        present_privacy = [field for field in privacy_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these privacy fields: {', '.join(present_privacy)}")
        
        # Validate privacy data structure if present
        if "privacy" in ip_intelligence_data:
            privacy_data = ip_intelligence_data["privacy"]
            assert isinstance(privacy_data, dict), "Privacy data should be a dictionary"
            
            # Check for privacy detection flags
            privacy_flags = ["vpn", "proxy", "tor", "relay", "hosting", "service"]
            present_flags = [flag for flag in privacy_flags if flag in privacy_data]
            print(f"Privacy detection for {test_ip} contains: {', '.join(present_flags)}")
            
            # Validate boolean privacy flags
            for flag in present_flags:
                if privacy_data[flag] is not None:
                    assert isinstance(privacy_data[flag], bool), f"Privacy flag {flag} should be boolean"
        
        # Check for hosting and infrastructure analysis
        hosting_fields = ["hosting"]
        present_hosting = [field for field in hosting_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these hosting fields: {', '.join(present_hosting)}")
        
        # Validate hosting data if present
        if "hosting" in ip_intelligence_data:
            hosting_data = ip_intelligence_data["hosting"]
            assert isinstance(hosting_data, dict), "Hosting data should be a dictionary"
            
            hosting_info_fields = ["host", "name", "network"]
            present_hosting_info = [field for field in hosting_info_fields if field in hosting_data]
            print(f"Hosting info for {test_ip} contains: {', '.join(present_hosting_info)}")
        
        # Check for abuse contact information
        abuse_fields = ["abuse"]
        present_abuse = [field for field in abuse_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these abuse fields: {', '.join(present_abuse)}")
        
        # Validate abuse contact data if present
        if "abuse" in ip_intelligence_data:
            abuse_data = ip_intelligence_data["abuse"]
            assert isinstance(abuse_data, dict), "Abuse data should be a dictionary"
            
            abuse_contact_fields = ["email", "name", "phone", "country", "network"]
            present_abuse_contact = [field for field in abuse_contact_fields if field in abuse_data]
            print(f"Abuse contact for {test_ip} contains: {', '.join(present_abuse_contact)}")
        
        # Check for domain and DNS information
        domain_fields = ["domains"]
        present_domains = [field for field in domain_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these domain fields: {', '.join(present_domains)}")
        
        # Validate domains data if present
        if "domains" in ip_intelligence_data:
            domains_data = ip_intelligence_data["domains"]
            assert isinstance(domains_data, dict), "Domains data should be a dictionary"
            
            domain_info_fields = ["total", "domains"]
            present_domain_info = [field for field in domain_info_fields if field in domains_data]
            print(f"Domain info for {test_ip} contains: {', '.join(present_domain_info)}")
            
            # Validate domain count if present
            if "total" in domains_data:
                total_domains = domains_data["total"]
                assert isinstance(total_domains, int), "Total domains should be an integer"
                assert total_domains >= 0, "Total domains should be non-negative"
        
        # Check for carrier and mobile network information
        carrier_fields = ["carrier"]
        present_carrier = [field for field in carrier_fields if field in ip_intelligence_data]
        if present_carrier:
            print(f"IP {test_ip} contains these carrier fields: {', '.join(present_carrier)}")
            
            carrier_data = ip_intelligence_data["carrier"]
            if isinstance(carrier_data, dict):
                carrier_info_fields = ["name", "mcc", "mnc"]
                present_carrier_info = [field for field in carrier_info_fields if field in carrier_data]
                print(f"Carrier info contains: {', '.join(present_carrier_info)}")
        
        # Check for ASN and network information
        asn_fields = ["asn"]
        present_asn = [field for field in asn_fields if field in ip_intelligence_data]
        if present_asn:
            print(f"IP {test_ip} contains these ASN fields: {', '.join(present_asn)}")
            
            asn_data = ip_intelligence_data["asn"]
            if isinstance(asn_data, dict):
                asn_info_fields = ["asn", "name", "domain", "route", "type"]
                present_asn_info = [field for field in asn_info_fields if field in asn_data]
                print(f"ASN info contains: {', '.join(present_asn_info)}")
        
        # Check for security and threat indicators
        security_fields = ["anycast", "bogon"]
        present_security = [field for field in security_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these security fields: {', '.join(present_security)}")
        
        # Validate security flags
        if "bogon" in ip_intelligence_data:
            bogon = ip_intelligence_data["bogon"]
            assert isinstance(bogon, bool), "Bogon status should be boolean"
        
        if "anycast" in ip_intelligence_data:
            anycast = ip_intelligence_data["anycast"]
            assert isinstance(anycast, bool), "Anycast status should be boolean"
        
        # Check for geolocation context (basic location info)
        geo_fields = ["country", "region", "city", "org"]
        present_geo = [field for field in geo_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these geographic fields: {', '.join(present_geo)}")
        
        # Check for company and organization details
        company_fields = ["company"]
        present_company = [field for field in company_fields if field in ip_intelligence_data]
        if present_company:
            print(f"IP {test_ip} contains these company fields: {', '.join(present_company)}")
            
            company_data = ip_intelligence_data["company"]
            if isinstance(company_data, dict):
                company_info_fields = ["name", "domain", "type"]
                present_company_info = [field for field in company_info_fields if field in company_data]
                print(f"Company info contains: {', '.join(present_company_info)}")
        
        # Log the structure of the first result for debugging
        if test_ip == test_ip_addresses[0]:
            print(f"Example IP intelligence structure: {ip_intelligence_data}")

        # Brief delay between requests to respect rate limiting
        import asyncio
        await asyncio.sleep(0.1)

    print(f"Successfully retrieved and validated IPInfo IP intelligence data for {len(test_ip_addresses)} IP addresses")

    return True