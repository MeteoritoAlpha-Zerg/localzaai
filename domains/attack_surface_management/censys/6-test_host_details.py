# 6-test_host_details.py

async def test_host_details(zerg_state=None):
    """Test Censys host details retrieval by way of connector tools"""
    print("Attempting to authenticate using Censys connector")

    assert zerg_state, "this test requires valid zerg_state"

    censys_api_id = zerg_state.get("censys_api_id").get("value")
    censys_api_secret = zerg_state.get("censys_api_secret").get("value")
    censys_base_url = zerg_state.get("censys_base_url").get("value")

    from connectors.censys.config import CensysConnectorConfig
    from connectors.censys.connector import CensysConnector
    from connectors.censys.tools import CensysConnectorTools, GetHostDetailsInput
    from connectors.censys.target import CensysTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = CensysConnectorConfig(
        api_id=censys_api_id,
        api_secret=censys_api_secret,
        base_url=censys_base_url
    )
    assert isinstance(config, ConnectorConfig), "CensysConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CensysConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CensysConnector should be of type Connector"

    # get query target options
    censys_query_target_options = await connector.get_query_target_options()
    assert isinstance(censys_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select search indices to target
    index_selector = None
    for selector in censys_query_target_options.selectors:
        if selector.type == 'search_indices':  
            index_selector = selector
            break

    assert index_selector, "failed to retrieve search index selector from query target options"

    assert isinstance(index_selector.values, list), "index_selector values must be a list"
    search_index = "hosts"  # Default to hosts index for this test
    
    # Verify hosts index is available
    assert search_index in index_selector.values, f"hosts index not available in search indices: {index_selector.values}"
    
    print(f"Selecting search index: {search_index}")

    # set up the target with search indices
    target = CensysTarget(search_indices=[search_index])
    assert isinstance(target, ConnectorTargetInterface), "CensysTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # First, get a host IP from search to use for detailed lookup
    search_hosts_tool = next(tool for tool in tools if tool.name == "search_censys_hosts")
    search_result = await search_hosts_tool.execute(query="services.service_name: HTTP", per_page=1)
    search_hosts = search_result.result
    
    assert isinstance(search_hosts, list), "search_hosts should be a list"
    assert len(search_hosts) > 0, "search_hosts should not be empty"
    
    target_ip = search_hosts[0]["ip"]
    print(f"Using target IP for detailed lookup: {target_ip}")

    # grab the get_censys_host_details tool and execute it with the target IP
    get_host_details_tool = next(tool for tool in tools if tool.name == "get_censys_host_details")
    host_details_result = await get_host_details_tool.execute(ip_address=target_ip)
    host_details = host_details_result.result

    print("Type of returned host_details:", type(host_details))
    print(f"host details: {str(host_details)[:200]}")

    # Verify that host_details is a dictionary
    assert isinstance(host_details, dict), "host_details should be a dictionary"
    assert len(host_details) > 0, "host_details should not be empty"
    
    # Verify essential Censys host detail fields
    assert "ip" in host_details, "Host details should have an 'ip' field"
    assert host_details["ip"] == target_ip, f"Returned IP {host_details['ip']} should match requested IP {target_ip}"
    
    # Verify IP address format (basic validation)
    ip_address = host_details["ip"]
    assert isinstance(ip_address, str), "IP address should be a string"
    assert len(ip_address.split(".")) == 4 or ":" in ip_address, "IP should be IPv4 or IPv6 format"
    
    # Check for services array which contains detailed port/service data
    assert "services" in host_details, "Host details should have a 'services' field"
    services = host_details["services"]
    assert isinstance(services, list), "Services should be a list"
    
    # Check detailed structure of services
    if len(services) > 0:
        service = services[0]  # Check first service in detail
        
        # Essential service fields for detailed view
        essential_service_fields = ["port", "service_name", "transport_protocol"]
        for field in essential_service_fields:
            if field in service:
                print(f"Service contains essential field: {field} = {service[field]}")
        
        # Additional detailed service fields
        detailed_service_fields = ["banner", "certificate", "software", "extended_service_name"]
        present_detailed = [field for field in detailed_service_fields if field in service]
        print(f"Service contains these detailed fields: {', '.join(present_detailed)}")
    
    # Check for additional detailed host fields (more comprehensive than search results)
    detailed_host_fields = ["location", "autonomous_system", "last_updated_at", "dns", "operating_system"]
    present_detailed_host = [field for field in detailed_host_fields if field in host_details]
    print(f"Host details contains these fields: {', '.join(present_detailed_host)}")
    
    # Verify location data if present (should be more detailed than search)
    if "location" in host_details:
        location = host_details["location"]
        assert isinstance(location, dict), "Location should be a dictionary"
        
        # Check for detailed location fields
        detailed_location_fields = ["country", "country_code", "city", "province", "postal_code", "coordinates", "timezone"]
        present_location = [field for field in detailed_location_fields if field in location]
        print(f"Host location contains: {', '.join(present_location)}")
        
        # Verify coordinates if present
        if "coordinates" in location:
            coords = location["coordinates"]
            assert isinstance(coords, dict), "Coordinates should be a dictionary"
            if "latitude" in coords and "longitude" in coords:
                print(f"Host coordinates: {coords['latitude']}, {coords['longitude']}")
    
    # Check for autonomous system details
    if "autonomous_system" in host_details:
        asn_info = host_details["autonomous_system"]
        assert isinstance(asn_info, dict), "Autonomous system should be a dictionary"
        
        asn_fields = ["asn", "name", "country_code", "organization"]
        present_asn = [field for field in asn_fields if field in asn_info]
        print(f"ASN info contains: {', '.join(present_asn)}")
    
    # Check for DNS information
    if "dns" in host_details:
        dns_info = host_details["dns"]
        if isinstance(dns_info, dict):
            dns_fields = ["reverse_dns", "names"]
            present_dns = [field for field in dns_fields if field in dns_info]
            print(f"DNS info contains: {', '.join(present_dns)}")
    
    # Log the full structure for debugging
    print(f"Example host details structure keys: {list(host_details.keys())}")

    print(f"Successfully retrieved and validated detailed information for host {target_ip}")

    return True