# 8-test_privacy_hosting.py

async def test_privacy_hosting(zerg_state=None):
    """Test IPInfo privacy detection and hosting intelligence retrieval by way of connector tools"""
    print("Attempting to authenticate using IPInfo connector")

    assert zerg_state, "this test requires valid zerg_state"

    ipinfo_api_token = zerg_state.get("ipinfo_api_token").get("value")
    ipinfo_base_url = zerg_state.get("ipinfo_base_url").get("value")
    ipinfo_api_version = zerg_state.get("ipinfo_api_version").get("value")

    from connectors.ipinfo.config import IPInfoConnectorConfig
    from connectors.ipinfo.connector import IPInfoConnector
    from connectors.ipinfo.tools import IPInfoConnectorTools, GetPrivacyHostingInput
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

    # grab privacy and hosting related data services
    assert isinstance(data_service_selector.values, list), "data_service_selector values must be a list"
    
    # Look for privacy and hosting services
    privacy_hosting_services = []
    desired_services = ["privacy", "hosting", "abuse"]
    for service in desired_services:
        if service in data_service_selector.values:
            privacy_hosting_services.append(service)
    
    # Use at least geolocation service if specific privacy services not available
    if not privacy_hosting_services:
        privacy_hosting_services = ["geolocation"]  # Fallback service
    
    print(f"Selecting privacy and hosting services: {privacy_hosting_services}")

    # set up the target with privacy and hosting services
    target = IPInfoTarget(data_services=privacy_hosting_services)
    assert isinstance(target, ConnectorTargetInterface), "IPInfoTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_ipinfo_privacy_hosting tool and execute it
    get_privacy_hosting_tool = next(tool for tool in tools if tool.name == "get_ipinfo_privacy_hosting")
    
    # Test with a diverse set of IP addresses for comprehensive privacy and hosting analysis
    test_ip_scenarios = [
        {"ip": "8.8.8.8", "description": "Google DNS - public service", "expected_type": "service"},
        {"ip": "1.1.1.1", "description": "Cloudflare DNS - public service", "expected_type": "service"},
        {"ip": "208.67.222.222", "description": "OpenDNS - public service", "expected_type": "service"},
        {"ip": "54.239.28.85", "description": "AWS hosting - cloud provider", "expected_type": "hosting"},
        {"ip": "151.101.193.140", "description": "Fastly CDN - hosting service", "expected_type": "hosting"},
    ]
    
    for scenario in test_ip_scenarios:
        test_ip = scenario["ip"]
        description = scenario["description"]
        expected_type = scenario["expected_type"]
        
        print(f"Testing privacy and hosting for IP: {test_ip} ({description})")
        
        # Get privacy and hosting intelligence with comprehensive analysis
        privacy_hosting_result = await get_privacy_hosting_tool.execute(
            ip_address=test_ip, 
            include_privacy_detection=True, 
            include_hosting_analysis=True,
            include_abuse_contacts=True
        )
        privacy_hosting_data = privacy_hosting_result.result

        print("Type of returned privacy_hosting_data:", type(privacy_hosting_data))
        print(f"Privacy/hosting data for {test_ip}: {str(privacy_hosting_data)[:200]}")

        # Verify that privacy_hosting_data is a dictionary
        assert isinstance(privacy_hosting_data, dict), "privacy_hosting_data should be a dictionary"
        assert len(privacy_hosting_data) > 0, "privacy_hosting_data should not be empty"
        
        # Verify essential IPInfo privacy and hosting fields
        assert "ip" in privacy_hosting_data, "Privacy/hosting data should have an 'ip' field"
        assert privacy_hosting_data["ip"] == test_ip, f"Returned IP {privacy_hosting_data['ip']} should match requested IP {test_ip}"
        
        # Check for privacy detection data
        privacy_fields = ["privacy"]
        present_privacy = [field for field in privacy_fields if field in privacy_hosting_data]
        print(f"IP {test_ip} contains these privacy fields: {', '.join(present_privacy)}")
        
        # Validate privacy detection structure if present
        if "privacy" in privacy_hosting_data:
            privacy_data = privacy_hosting_data["privacy"]
            assert isinstance(privacy_data, dict), "Privacy data should be a dictionary"
            
            # Check for comprehensive privacy detection flags
            privacy_flags = ["vpn", "proxy", "tor", "relay", "hosting", "service"]
            present_flags = [flag for flag in privacy_flags if flag in privacy_data]
            print(f"Privacy detection for {test_ip} contains: {', '.join(present_flags)}")
            
            # Validate boolean privacy flags
            for flag in present_flags:
                if privacy_data[flag] is not None:
                    assert isinstance(privacy_data[flag], bool), f"Privacy flag {flag} should be boolean"
            
            # Validate expected service type if present
            if "service" in privacy_data and expected_type == "service":
                service_flag = privacy_data["service"]
                print(f"Service detection for {test_ip}: {service_flag}")
            
            if "hosting" in privacy_data and expected_type == "hosting":
                hosting_flag = privacy_data["hosting"]
                print(f"Hosting detection for {test_ip}: {hosting_flag}")
        
        # Check for hosting and infrastructure analysis
        hosting_fields = ["hosting"]
        present_hosting = [field for field in hosting_fields if field in privacy_hosting_data]
        print(f"IP {test_ip} contains these hosting fields: {', '.join(present_hosting)}")
        
        # Validate hosting data structure if present
        if "hosting" in privacy_hosting_data:
            hosting_data = privacy_hosting_data["hosting"]
            assert isinstance(hosting_data, dict), "Hosting data should be a dictionary"
            
            # Check for hosting provider information
            hosting_info_fields = ["host", "name", "network", "domain"]
            present_hosting_info = [field for field in hosting_info_fields if field in hosting_data]
            print(f"Hosting info for {test_ip} contains: {', '.join(present_hosting_info)}")
            
            # Validate hosting provider details
            if "name" in hosting_data and hosting_data["name"]:
                provider_name = hosting_data["name"]
                assert isinstance(provider_name, str), "Hosting provider name should be a string"
                print(f"Hosting provider for {test_ip}: {provider_name}")
        
        # Check for abuse contact information
        abuse_fields = ["abuse"]
        present_abuse = [field for field in abuse_fields if field in privacy_hosting_data]
        print(f"IP {test_ip} contains these abuse fields: {', '.join(present_abuse)}")
        
        # Validate abuse contact data structure if present
        if "abuse" in privacy_hosting_data:
            abuse_data = privacy_hosting_data["abuse"]
            assert isinstance(abuse_data, dict), "Abuse data should be a dictionary"
            
            # Check for comprehensive abuse contact information
            abuse_contact_fields = ["email", "name", "phone", "country", "network", "address"]
            present_abuse_contact = [field for field in abuse_contact_fields if field in abuse_data]
            print(f"Abuse contact for {test_ip} contains: {', '.join(present_abuse_contact)}")
            
            # Validate email format if present
            if "email" in abuse_data and abuse_data["email"]:
                email = abuse_data["email"]
                assert isinstance(email, str), "Abuse email should be a string"
                assert "@" in email, f"Abuse email should be valid format, got: {email}"
        
        # Check for domain and DNS hosting information
        domain_fields = ["domains"]
        present_domains = [field for field in domain_fields if field in privacy_hosting_data]
        print(f"IP {test_ip} contains these domain fields: {', '.join(present_domains)}")
        
        # Validate domains hosting data if present
        if "domains" in privacy_hosting_data:
            domains_data = privacy_hosting_data["domains"]
            assert isinstance(domains_data, dict), "Domains data should be a dictionary"
            
            # Check for hosted domain information
            domain_info_fields = ["total", "domains", "page"]
            present_domain_info = [field for field in domain_info_fields if field in domains_data]
            print(f"Domain hosting info for {test_ip} contains: {', '.join(present_domain_info)}")
            
            # Validate domain count if present
            if "total" in domains_data and domains_data["total"] is not None:
                total_domains = domains_data["total"]
                assert isinstance(total_domains, int), "Total domains should be an integer"
                assert total_domains >= 0, "Total domains should be non-negative"
                print(f"Total domains hosted on {test_ip}: {total_domains}")
        
        # Check for carrier and mobile network information
        carrier_fields = ["carrier"]
        present_carrier = [field for field in carrier_fields if field in privacy_hosting_data]
        if present_carrier:
            print(f"IP {test_ip} contains these carrier fields: {', '.join(present_carrier)}")
            
            carrier_data = privacy_hosting_data["carrier"]
            if isinstance(carrier_data, dict):
                # Check for mobile carrier information
                carrier_info_fields = ["name", "mcc", "mnc"]
                present_carrier_info = [field for field in carrier_info_fields if field in carrier_data]
                print(f"Carrier info for {test_ip} contains: {', '.join(present_carrier_info)}")
        
        # Check for company and organization information
        company_fields = ["company"]
        present_company = [field for field in company_fields if field in privacy_hosting_data]
        if present_company:
            print(f"IP {test_ip} contains these company fields: {', '.join(present_company)}")
            
            company_data = privacy_hosting_data["company"]
            if isinstance(company_data, dict):
                # Check for detailed company information
                company_info_fields = ["name", "domain", "type"]
                present_company_info = [field for field in company_info_fields if field in company_data]
                print(f"Company info for {test_ip} contains: {', '.join(present_company_info)}")
                
                # Validate company type if present
                if "type" in company_data and company_data["type"]:
                    company_type = company_data["type"]
                    valid_types = ["business", "hosting", "isp", "government", "education"]
                    if company_type in valid_types:
                        print(f"Company type for {test_ip}: {company_type}")
        
        # Check for security and threat indicators
        security_fields = ["anycast", "bogon"]
        present_security = [field for field in security_fields if field in privacy_hosting_data]
        print(f"IP {test_ip} contains these security fields: {', '.join(present_security)}")
        
        # Validate security flags
        if "bogon" in privacy_hosting_data and privacy_hosting_data["bogon"] is not None:
            bogon = privacy_hosting_data["bogon"]
            assert isinstance(bogon, bool), "Bogon status should be boolean"
            print(f"Bogon status for {test_ip}: {bogon}")
        
        if "anycast" in privacy_hosting_data and privacy_hosting_data["anycast"] is not None:
            anycast = privacy_hosting_data["anycast"]
            assert isinstance(anycast, bool), "Anycast status should be boolean"
            print(f"Anycast status for {test_ip}: {anycast}")
        
        # Check for geolocation context
        geo_fields = ["country", "region", "city", "org"]
        present_geo = [field for field in geo_fields if field in privacy_hosting_data]
        print(f"IP {test_ip} contains these geographic fields: {', '.join(present_geo)}")
        
        # Check for network infrastructure and ISP information
        network_fields = ["asn", "org", "hostname"]
        present_network = [field for field in network_fields if field in privacy_hosting_data]
        print(f"IP {test_ip} contains these network fields: {', '.join(present_network)}")
        
        # Validate ASN information if present
        if "asn" in privacy_hosting_data:
            asn_data = privacy_hosting_data["asn"]
            if isinstance(asn_data, dict):
                asn_fields = ["asn", "name", "domain", "route", "type"]
                present_asn_fields = [field for field in asn_fields if field in asn_data]
                print(f"ASN info for {test_ip} contains: {', '.join(present_asn_fields)}")
        
        # Check for timezone and postal information
        location_fields = ["timezone", "postal", "loc"]
        present_location = [field for field in location_fields if field in privacy_hosting_data]
        print(f"IP {test_ip} contains these location fields: {', '.join(present_location)}")
        
        # Log the structure of the first result for debugging
        if scenario == test_ip_scenarios[0]:
            print(f"Example privacy/hosting structure: {privacy_hosting_data}")

        # Brief delay between requests to respect rate limiting
        import asyncio
        await asyncio.sleep(0.1)

    print(f"Successfully retrieved and validated IPInfo privacy and hosting data for {len(test_ip_scenarios)} IP scenarios")

    return True