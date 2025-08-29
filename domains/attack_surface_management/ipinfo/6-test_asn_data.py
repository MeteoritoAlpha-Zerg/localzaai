# 6-test_asn_data.py

async def test_asn_data(zerg_state=None):
    """Test IPInfo ASN and network infrastructure data retrieval by way of connector tools"""
    print("Attempting to authenticate using IPInfo connector")

    assert zerg_state, "this test requires valid zerg_state"

    ipinfo_api_token = zerg_state.get("ipinfo_api_token").get("value")
    ipinfo_base_url = zerg_state.get("ipinfo_base_url").get("value")
    ipinfo_api_version = zerg_state.get("ipinfo_api_version").get("value")

    from connectors.ipinfo.config import IPInfoConnectorConfig
    from connectors.ipinfo.connector import IPInfoConnector
    from connectors.ipinfo.tools import IPInfoConnectorTools, GetASNDataInput
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

    # grab ASN data service
    assert isinstance(data_service_selector.values, list), "data_service_selector values must be a list"
    asn_service = "asn"  # Standard ASN service
    
    # Verify ASN service is available, fallback to geolocation if not
    if asn_service not in data_service_selector.values:
        asn_service = "geolocation"  # Fallback service that includes ASN data
    
    print(f"Selecting data service: {asn_service}")

    # set up the target with ASN data service
    target = IPInfoTarget(data_services=[asn_service])
    assert isinstance(target, ConnectorTargetInterface), "IPInfoTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_ipinfo_asn_data tool and execute it
    get_asn_data_tool = next(tool for tool in tools if tool.name == "get_ipinfo_asn_data")
    
    # Test with well-known ASNs and IP addresses
    test_scenarios = [
        {"type": "asn", "value": "AS15169", "description": "Google ASN"},
        {"type": "asn", "value": "AS13335", "description": "Cloudflare ASN"},
        {"type": "ip", "value": "8.8.8.8", "description": "Google DNS IP for ASN lookup"},
    ]
    
    for scenario in test_scenarios:
        lookup_type = scenario["type"]
        lookup_value = scenario["value"]
        description = scenario["description"]
        
        print(f"Testing ASN data for {lookup_type}: {lookup_value} ({description})")
        
        # Get ASN data with comprehensive network information
        if lookup_type == "asn":
            asn_result = await get_asn_data_tool.execute(
                asn=lookup_value,
                include_prefixes=True,
                include_peers=True
            )
        else:  # IP lookup
            asn_result = await get_asn_data_tool.execute(
                ip_address=lookup_value,
                include_asn_details=True
            )
        
        asn_data = asn_result.result

        print("Type of returned asn_data:", type(asn_data))
        print(f"ASN data for {lookup_value}: {str(asn_data)[:200]}")

        # Verify that asn_data is a dictionary
        assert isinstance(asn_data, dict), "asn_data should be a dictionary"
        assert len(asn_data) > 0, "asn_data should not be empty"
        
        # Verify essential IPInfo ASN fields
        if lookup_type == "asn":
            assert "asn" in asn_data, "ASN data should have an 'asn' field"
            assert asn_data["asn"] == lookup_value, f"Returned ASN {asn_data['asn']} should match requested ASN {lookup_value}"
        
        # Check for essential ASN information
        asn_fields = ["asn", "name", "country", "allocated", "registry"]
        present_asn = [field for field in asn_fields if field in asn_data]
        print(f"ASN {lookup_value} contains these ASN fields: {', '.join(present_asn)}")
        
        # Validate ASN format if present
        if "asn" in asn_data and asn_data["asn"]:
            asn = asn_data["asn"]
            assert isinstance(asn, str), "ASN should be a string"
            assert asn.startswith("AS"), f"ASN should start with 'AS', got: {asn}"
        
        # Validate country code if present
        if "country" in asn_data and asn_data["country"]:
            country = asn_data["country"]
            assert isinstance(country, str), "Country should be a string"
            assert len(country) == 2, f"Country code should be 2 characters, got: {country}"
        
        # Check for network prefixes and routes
        prefix_fields = ["prefixes", "prefixes6"]  # IPv4 and IPv6 prefixes
        present_prefixes = [field for field in prefix_fields if field in asn_data]
        print(f"ASN {lookup_value} contains these prefix fields: {', '.join(present_prefixes)}")
        
        # Validate prefixes structure if present
        if "prefixes" in asn_data:
            prefixes = asn_data["prefixes"]
            assert isinstance(prefixes, list), "IPv4 prefixes should be a list"
            
            for prefix in prefixes[:3]:  # Check first 3 prefixes
                prefix_fields = ["netblock", "id", "name", "country"]
                present_prefix_fields = [field for field in prefix_fields if field in prefix]
                print(f"IPv4 prefix contains: {', '.join(present_prefix_fields)}")
                
                # Validate netblock format
                if "netblock" in prefix:
                    netblock = prefix["netblock"]
                    assert isinstance(netblock, str), "Netblock should be a string"
                    assert "/" in netblock, f"Netblock should contain CIDR notation, got: {netblock}"
        
        # Check for IPv6 prefixes
        if "prefixes6" in asn_data:
            prefixes6 = asn_data["prefixes6"]
            assert isinstance(prefixes6, list), "IPv6 prefixes should be a list"
            
            for prefix6 in prefixes6[:2]:  # Check first 2 IPv6 prefixes
                prefix6_fields = ["netblock", "id", "name", "country"]
                present_prefix6_fields = [field for field in prefix6_fields if field in prefix6]
                print(f"IPv6 prefix contains: {', '.join(present_prefix6_fields)}")
        
        # Check for peering information
        peer_fields = ["peers"]
        present_peers = [field for field in peer_fields if field in asn_data]
        print(f"ASN {lookup_value} contains these peer fields: {', '.join(present_peers)}")
        
        # Validate peers structure if present
        if "peers" in asn_data:
            peers = asn_data["peers"]
            assert isinstance(peers, list), "Peers should be a list"
            
            for peer in peers[:3]:  # Check first 3 peers
                peer_fields = ["asn", "name", "country"]
                present_peer_fields = [field for field in peer_fields if field in peer]
                print(f"Peer contains: {', '.join(present_peer_fields)}")
                
                # Validate peer ASN format
                if "asn" in peer:
                    peer_asn = peer["asn"]
                    assert isinstance(peer_asn, str), "Peer ASN should be a string"
                    assert peer_asn.startswith("AS"), f"Peer ASN should start with 'AS', got: {peer_asn}"
        
        # Check for upstream and downstream information
        upstream_fields = ["upstreams", "downstreams"]
        present_upstream = [field for field in upstream_fields if field in asn_data]
        print(f"ASN {lookup_value} contains these upstream/downstream fields: {', '.join(present_upstream)}")
        
        # Check for domain and organization information
        org_fields = ["domain", "type"]  # ASN type (hosting, isp, business, education)
        present_org = [field for field in org_fields if field in asn_data]
        print(f"ASN {lookup_value} contains these organization fields: {', '.join(present_org)}")
        
        # Validate ASN type if present
        if "type" in asn_data and asn_data["type"]:
            asn_type = asn_data["type"]
            valid_types = ["hosting", "isp", "business", "education", "government", "unknown"]
            assert asn_type in valid_types, f"ASN type {asn_type} should be one of {valid_types}"
        
        # Check for geographical and network statistics
        stats_fields = ["num_ips", "num_prefixes", "num_prefixes6"]
        present_stats = [field for field in stats_fields if field in asn_data]
        print(f"ASN {lookup_value} contains these statistics fields: {', '.join(present_stats)}")
        
        # Validate statistics if present
        for stat_field in present_stats:
            if asn_data[stat_field] is not None:
                stat_value = asn_data[stat_field]
                assert isinstance(stat_value, int), f"Statistic {stat_field} should be an integer"
                assert stat_value >= 0, f"Statistic {stat_field} should be non-negative"
        
        # Check for additional network intelligence
        intel_fields = ["rank", "abuse_contacts"]
        present_intel = [field for field in intel_fields if field in asn_data]
        print(f"ASN {lookup_value} contains these intelligence fields: {', '.join(present_intel)}")
        
        # Validate abuse contacts if present
        if "abuse_contacts" in asn_data:
            abuse_contacts = asn_data["abuse_contacts"]
            assert isinstance(abuse_contacts, list), "Abuse contacts should be a list"
            
            for contact in abuse_contacts[:2]:  # Check first 2 contacts
                contact_fields = ["email", "name", "phone"]
                present_contact_fields = [field for field in contact_fields if field in contact]
                print(f"Abuse contact contains: {', '.join(present_contact_fields)}")
        
        # Log the structure of the first result for debugging
        if scenario == test_scenarios[0]:
            print(f"Example ASN data structure: {asn_data}")

        # Brief delay between requests to respect rate limiting
        import asyncio
        await asyncio.sleep(0.2)

    print(f"Successfully retrieved and validated IPInfo ASN data for {len(test_scenarios)} scenarios")

    return True