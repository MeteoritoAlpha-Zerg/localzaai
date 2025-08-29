# 5-test_host_search.py

async def test_host_search(zerg_state=None):
    """Test Censys host search by way of connector tools"""
    print("Attempting to authenticate using Censys connector")

    assert zerg_state, "this test requires valid zerg_state"

    censys_api_id = zerg_state.get("censys_api_id").get("value")
    censys_api_secret = zerg_state.get("censys_api_secret").get("value")
    censys_base_url = zerg_state.get("censys_base_url").get("value")

    from connectors.censys.config import CensysConnectorConfig
    from connectors.censys.connector import CensysConnector
    from connectors.censys.tools import CensysConnectorTools, SearchHostsInput
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

    # grab the search_censys_hosts tool and execute it with a basic query
    search_hosts_tool = next(tool for tool in tools if tool.name == "search_censys_hosts")
    
    # Use a basic search query that should return results
    search_query = "services.service_name: HTTP"
    hosts_result = await search_hosts_tool.execute(query=search_query, per_page=10)
    censys_hosts = hosts_result.result

    print("Type of returned censys_hosts:", type(censys_hosts))
    print(f"len hosts: {len(censys_hosts)} hosts: {str(censys_hosts)[:200]}")

    # Verify that censys_hosts is a list
    assert isinstance(censys_hosts, list), "censys_hosts should be a list"
    assert len(censys_hosts) > 0, "censys_hosts should not be empty"
    
    # Limit the number of hosts to check if there are many
    hosts_to_check = censys_hosts[:5] if len(censys_hosts) > 5 else censys_hosts
    
    # Verify structure of each host object
    for host in hosts_to_check:
        # Verify essential Censys host fields
        assert "ip" in host, "Each host should have an 'ip' field"
        
        # Verify IP address format (basic validation)
        ip_address = host["ip"]
        assert isinstance(ip_address, str), "IP address should be a string"
        assert len(ip_address.split(".")) == 4 or ":" in ip_address, "IP should be IPv4 or IPv6 format"
        
        # Check for services array which contains port/service data
        assert "services" in host, "Each host should have a 'services' field"
        services = host["services"]
        assert isinstance(services, list), "Services should be a list"
        
        # Check structure of services if any exist
        if len(services) > 0:
            service = services[0]  # Check first service
            
            # Essential service fields
            service_fields = ["port", "service_name", "transport_protocol"]
            for field in service_fields:
                if field in service:
                    print(f"Host {ip_address} service contains field: {field}")
        
        # Check for additional optional host fields
        optional_fields = ["location", "autonomous_system", "last_updated_at", "dns"]
        present_optional = [field for field in optional_fields if field in host]
        
        print(f"Host {ip_address} contains these optional fields: {', '.join(present_optional)}")
        
        # Verify location data if present
        if "location" in host:
            location = host["location"]
            assert isinstance(location, dict), "Location should be a dictionary"
            location_fields = ["country", "country_code", "city"]
            present_location = [field for field in location_fields if field in location]
            print(f"Host {ip_address} location contains: {', '.join(present_location)}")
        
        # Log the structure of the first host for debugging
        if host == hosts_to_check[0]:
            print(f"Example host structure: {host}")

    print(f"Successfully retrieved and validated {len(censys_hosts)} Censys hosts")

    return True