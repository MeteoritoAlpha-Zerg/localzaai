# 4-test_ip_geolocation.py

async def test_ip_geolocation(zerg_state=None):
    """Test IPInfo IP geolocation and geographic intelligence retrieval by way of connector tools"""
    print("Attempting to authenticate using IPInfo connector")

    assert zerg_state, "this test requires valid zerg_state"

    ipinfo_api_token = zerg_state.get("ipinfo_api_token").get("value")
    ipinfo_base_url = zerg_state.get("ipinfo_base_url").get("value")
    ipinfo_api_version = zerg_state.get("ipinfo_api_version").get("value")

    from connectors.ipinfo.config import IPInfoConnectorConfig
    from connectors.ipinfo.connector import IPInfoConnector
    from connectors.ipinfo.tools import IPInfoConnectorTools
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

    # grab geolocation data service
    assert isinstance(data_service_selector.values, list), "data_service_selector values must be a list"
    geolocation_service = "geolocation"  # Standard geolocation service
    
    # Verify geolocation service is available
    assert geolocation_service in data_service_selector.values, f"geolocation service not available in data services: {data_service_selector.values}"
    
    print(f"Selecting data service: {geolocation_service}")

    # set up the target with data services
    target = IPInfoTarget(data_services=[geolocation_service])
    assert isinstance(target, ConnectorTargetInterface), "IPInfoTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_ipinfo_geolocation tool
    get_geolocation_tool = next(tool for tool in tools if tool.name == "get_ipinfo_geolocation")
    
    # Test with well-known public IP addresses for reliable geolocation data
    test_ip_addresses = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]  # Google DNS, Cloudflare, OpenDNS
    
    for test_ip in test_ip_addresses:
        print(f"Testing geolocation for IP: {test_ip}")
        
        geolocation_result = await get_geolocation_tool.execute(
            ip_address=test_ip, 
            include_hostname=True, 
            include_company=True
        )
        geolocation_data = geolocation_result.result

        print("Type of returned geolocation_data:", type(geolocation_data))
        print(f"geolocation data for {test_ip}: {str(geolocation_data)[:200]}")

        # Verify that geolocation_data is a dictionary
        assert isinstance(geolocation_data, dict), "geolocation_data should be a dictionary"
        assert len(geolocation_data) > 0, "geolocation_data should not be empty"
        
        # Verify essential IPInfo geolocation fields
        assert "ip" in geolocation_data, "Geolocation data should have an 'ip' field"
        assert geolocation_data["ip"] == test_ip, f"Returned IP {geolocation_data['ip']} should match requested IP {test_ip}"
        
        # Check for essential location fields
        location_fields = ["country", "region", "city"]
        for field in location_fields:
            assert field in geolocation_data, f"Geolocation data should contain '{field}' field"
        
        # Verify country code format if present
        if "country" in geolocation_data and geolocation_data["country"]:
            country = geolocation_data["country"]
            assert isinstance(country, str), "Country should be a string"
            assert len(country) == 2, f"Country code should be 2 characters, got: {country}"
        
        # Check for coordinate information
        coordinate_fields = ["loc"]  # IPInfo uses "loc" field for coordinates
        present_coordinates = [field for field in coordinate_fields if field in geolocation_data]
        print(f"IP {test_ip} contains these coordinate fields: {', '.join(present_coordinates)}")
        
        # Validate coordinates if present
        if "loc" in geolocation_data and geolocation_data["loc"]:
            loc = geolocation_data["loc"]
            assert isinstance(loc, str), "Location coordinates should be a string"
            # IPInfo format: "latitude,longitude"
            if "," in loc:
                lat_str, lon_str = loc.split(",")
                lat = float(lat_str)
                lon = float(lon_str)
                assert -90 <= lat <= 90, f"Latitude should be between -90 and 90, got: {lat}"
                assert -180 <= lon <= 180, f"Longitude should be between -180 and 180, got: {lon}"
        
        # Check for ISP and organization information
        isp_fields = ["org", "hostname"]  # IPInfo uses "org" for organization
        present_isp = [field for field in isp_fields if field in geolocation_data]
        print(f"IP {test_ip} contains these ISP fields: {', '.join(present_isp)}")
        
        # Check for postal and timezone information
        postal_fields = ["postal", "timezone"]
        present_postal = [field for field in postal_fields if field in geolocation_data]
        print(f"IP {test_ip} contains these postal fields: {', '.join(present_postal)}")
        
        # Check for additional IPInfo specific fields
        ipinfo_fields = ["anycast", "bogon"]  # IPInfo specific fields
        present_ipinfo = [field for field in ipinfo_fields if field in geolocation_data]
        print(f"IP {test_ip} contains these IPInfo fields: {', '.join(present_ipinfo)}")
        
        # Validate bogon status if present
        if "bogon" in geolocation_data:
            bogon = geolocation_data["bogon"]
            assert isinstance(bogon, bool), "Bogon status should be boolean"
        
        # Check for company information if requested
        if "company" in geolocation_data:
            company = geolocation_data["company"]
            assert isinstance(company, dict), "Company info should be a dictionary"
            
            company_fields = ["name", "domain", "type"]
            present_company = [field for field in company_fields if field in company]
            print(f"Company info for {test_ip} contains: {', '.join(present_company)}")
        
        # Check for abuse contact information
        abuse_fields = ["abuse"]
        present_abuse = [field for field in abuse_fields if field in geolocation_data]
        if present_abuse:
            print(f"IP {test_ip} contains abuse contact fields: {', '.join(present_abuse)}")
            
            abuse = geolocation_data["abuse"]
            if isinstance(abuse, dict):
                abuse_contact_fields = ["email", "name", "network", "country"]
                present_abuse_contact = [field for field in abuse_contact_fields if field in abuse]
                print(f"Abuse contact contains: {', '.join(present_abuse_contact)}")
        
        # Log the structure of the first result for debugging
        if test_ip == test_ip_addresses[0]:
            print(f"Example geolocation structure: {geolocation_data}")

        # Brief delay between requests to respect rate limiting
        import asyncio
        await asyncio.sleep(0.1)

    print(f"Successfully retrieved and validated IPInfo geolocation data for {len(test_ip_addresses)} IP addresses")

    return True