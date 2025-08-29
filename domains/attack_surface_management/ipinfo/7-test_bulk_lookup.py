# 7-test_bulk_lookup.py

async def test_bulk_lookup(zerg_state=None):
    """Test IPInfo bulk IP lookup and batch processing by way of connector tools"""
    print("Attempting to authenticate using IPInfo connector")

    assert zerg_state, "this test requires valid zerg_state"

    ipinfo_api_token = zerg_state.get("ipinfo_api_token").get("value")
    ipinfo_base_url = zerg_state.get("ipinfo_base_url").get("value")
    ipinfo_api_version = zerg_state.get("ipinfo_api_version").get("value")

    from connectors.ipinfo.config import IPInfoConnectorConfig
    from connectors.ipinfo.connector import IPInfoConnector
    from connectors.ipinfo.tools import IPInfoConnectorTools, BulkIPLookupInput
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

    # select multiple data services for comprehensive bulk analysis
    data_service_selector = None
    for selector in ipinfo_query_target_options.selectors:
        if selector.type == 'data_services':  
            data_service_selector = selector
            break

    assert data_service_selector, "failed to retrieve data service selector from query target options"

    # grab multiple data services for bulk analysis
    assert isinstance(data_service_selector.values, list), "data_service_selector values must be a list"
    
    # Select multiple services for comprehensive bulk analysis
    desired_services = ["geolocation", "privacy", "abuse", "hosting"]
    available_services = [service for service in desired_services if service in data_service_selector.values]
    
    # Ensure at least geolocation is available
    if not available_services:
        available_services = ["geolocation"]
    
    print(f"Selecting data services for bulk analysis: {available_services}")

    # set up the target with multiple data services
    target = IPInfoTarget(data_services=available_services)
    assert isinstance(target, ConnectorTargetInterface), "IPInfoTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the bulk_ip_lookup tool and execute it
    bulk_lookup_tool = next(tool for tool in tools if tool.name == "bulk_ip_lookup")
    
    # Create a comprehensive test dataset with various IP types
    test_ip_list = [
        # Public DNS servers
        "8.8.8.8", "8.8.4.4",  # Google DNS
        "1.1.1.1", "1.0.0.1",  # Cloudflare DNS
        "208.67.222.222", "208.67.220.220",  # OpenDNS
        "9.9.9.9", "149.112.112.112",  # Quad9 DNS
        # Major websites and services
        "142.250.191.14",  # Google
        "157.240.11.35",   # Facebook
        "13.107.42.14",    # Microsoft
        "54.239.28.85",    # AWS
        # CDN and cloud providers
        "151.101.193.140",  # Fastly
        "104.16.132.229",   # Cloudflare CDN
    ]
    
    print(f"Testing bulk lookup with {len(test_ip_list)} IP addresses")
    
    # Perform bulk IP lookup with comprehensive options
    bulk_result = await bulk_lookup_tool.execute(
        ip_addresses=test_ip_list,
        include_hostname=True,
        include_company=True,
        include_privacy=True,
        include_abuse=True,
        batch_size=len(test_ip_list)  # Process all IPs in one batch
    )
    bulk_lookup_data = bulk_result.result

    print("Type of returned bulk_lookup_data:", type(bulk_lookup_data))
    print(f"Bulk lookup completed for {len(test_ip_list)} IPs: {str(bulk_lookup_data)[:200]}")

    # Verify that bulk_lookup_data is a dictionary with results
    assert isinstance(bulk_lookup_data, dict), "bulk_lookup_data should be a dictionary"
    assert len(bulk_lookup_data) > 0, "bulk_lookup_data should not be empty"
    
    # IPInfo bulk API returns IP addresses as keys with their data as values
    # Verify we have results for all requested IPs
    returned_ips = set(bulk_lookup_data.keys())
    requested_ips = set(test_ip_list)
    
    print(f"Requested IPs: {len(requested_ips)}, Returned IPs: {len(returned_ips)}")
    
    # Check that we got results for all requested IPs
    missing_ips = requested_ips - returned_ips
    if missing_ips:
        print(f"Missing results for IPs: {missing_ips}")
        # Allow some missing results but ensure we got most of them
        assert len(returned_ips) >= len(requested_ips) * 0.8, "Should get results for at least 80% of requested IPs"
    
    # Process individual IP results
    results_to_check = list(bulk_lookup_data.items())[:5] if len(bulk_lookup_data) > 5 else list(bulk_lookup_data.items())
    
    # Verify structure of individual IP lookup results
    for ip_address, ip_data in results_to_check:
        print(f"Validating bulk result for IP: {ip_address}")
        
        # Verify IP is from our test list
        assert ip_address in test_ip_list, f"Result IP {ip_address} should be from test list"
        
        # Verify IP data structure
        assert isinstance(ip_data, dict), f"IP data for {ip_address} should be a dictionary"
        assert len(ip_data) > 0, f"IP data for {ip_address} should not be empty"
        
        # Check for essential geolocation fields
        geo_fields = ["ip", "country", "region", "city"]
        present_geo = [field for field in geo_fields if field in ip_data]
        print(f"IP {ip_address} geolocation fields: {', '.join(present_geo)}")
        
        # Verify IP matches
        if "ip" in ip_data:
            assert ip_data["ip"] == ip_address, f"IP field should match key: {ip_data['ip']} vs {ip_address}"
        
        # Check for ISP and organization data
        isp_fields = ["org", "hostname"]
        present_isp = [field for field in isp_fields if field in ip_data]
        print(f"IP {ip_address} ISP fields: {', '.join(present_isp)}")
        
        # Check for privacy data if included
        privacy_fields = ["privacy"]
        present_privacy = [field for field in privacy_fields if field in ip_data]
        if present_privacy:
            print(f"IP {ip_address} privacy fields: {', '.join(present_privacy)}")
            
            privacy_data = ip_data["privacy"]
            if isinstance(privacy_data, dict):
                privacy_flags = ["vpn", "proxy", "tor", "relay", "hosting"]
                present_flags = [flag for flag in privacy_flags if flag in privacy_data]
                print(f"Privacy flags for {ip_address}: {', '.join(present_flags)}")
        
        # Check for abuse contact data if included
        abuse_fields = ["abuse"]
        present_abuse = [field for field in abuse_fields if field in ip_data]
        if present_abuse:
            print(f"IP {ip_address} abuse fields: {', '.join(present_abuse)}")
            
            abuse_data = ip_data["abuse"]
            if isinstance(abuse_data, dict):
                abuse_contact_fields = ["email", "name", "country"]
                present_contacts = [field for field in abuse_contact_fields if field in abuse_data]
                print(f"Abuse contacts for {ip_address}: {', '.join(present_contacts)}")
        
        # Check for company data if included
        company_fields = ["company"]
        present_company = [field for field in company_fields if field in ip_data]
        if present_company:
            print(f"IP {ip_address} company fields: {', '.join(present_company)}")
            
            company_data = ip_data["company"]
            if isinstance(company_data, dict):
                company_info_fields = ["name", "domain", "type"]
                present_company_info = [field for field in company_info_fields if field in company_data]
                print(f"Company info for {ip_address}: {', '.join(present_company_info)}")
        
        # Check for coordinate data
        if "loc" in ip_data and ip_data["loc"]:
            loc = ip_data["loc"]
            assert isinstance(loc, str), f"Location coordinates should be a string for {ip_address}"
            if "," in loc:
                lat_str, lon_str = loc.split(",")
                lat = float(lat_str)
                lon = float(lon_str)
                assert -90 <= lat <= 90, f"Latitude should be valid for {ip_address}"
                assert -180 <= lon <= 180, f"Longitude should be valid for {ip_address}"
        
        # Check for security flags
        security_fields = ["anycast", "bogon"]
        present_security = [field for field in security_fields if field in ip_data]
        if present_security:
            print(f"IP {ip_address} security fields: {', '.join(present_security)}")
    
    # Check for bulk operation metadata (if provided by connector)
    metadata_fields = ["request_count", "response_count", "processing_time", "rate_limit_info"]
    if any(field in bulk_lookup_data for field in metadata_fields):
        print("Bulk operation includes metadata")
        
        if "request_count" in bulk_lookup_data:
            request_count = bulk_lookup_data["request_count"]
            assert request_count == len(test_ip_list), "Request count should match input"
        
        if "response_count" in bulk_lookup_data:
            response_count = bulk_lookup_data["response_count"]
            assert response_count <= len(test_ip_list), "Response count should not exceed requests"
    
    # Validate data consistency across results
    countries = set()
    organizations = set()
    
    for ip_address, ip_data in bulk_lookup_data.items():
        if isinstance(ip_data, dict):
            if "country" in ip_data and ip_data["country"]:
                countries.add(ip_data["country"])
            if "org" in ip_data and ip_data["org"]:
                organizations.add(ip_data["org"])
    
    print(f"Bulk lookup found {len(countries)} unique countries and {len(organizations)} unique organizations")
    
    # Ensure we have reasonable diversity in results
    assert len(countries) >= 1, "Should have at least 1 country in results"
    assert len(organizations) >= 3, "Should have at least 3 different organizations in results"
    
    # Log overall bulk operation results
    print(f"Bulk lookup structure: {len(bulk_lookup_data)} IP results")
    
    # Log example result structure
    if results_to_check:
        example_ip, example_data = results_to_check[0]
        print(f"Example bulk result structure for {example_ip}: {list(example_data.keys())}")

    print(f"Successfully completed bulk lookup of {len(test_ip_list)} IP addresses")

    return True