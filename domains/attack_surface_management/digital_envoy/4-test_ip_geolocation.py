# 4-test_ip_geolocation.py

async def test_ip_geolocation(zerg_state=None):
    """Test Digital Envoy IP geolocation and location intelligence retrieval by way of connector tools"""
    print("Attempting to authenticate using Digital Envoy connector")

    assert zerg_state, "this test requires valid zerg_state"

    digital_envoy_api_key = zerg_state.get("digital_envoy_api_key").get("value")
    digital_envoy_api_secret = zerg_state.get("digital_envoy_api_secret").get("value")
    digital_envoy_base_url = zerg_state.get("digital_envoy_base_url").get("value")
    digital_envoy_api_version = zerg_state.get("digital_envoy_api_version").get("value")

    from connectors.digital_envoy.config import DigitalEnvoyConnectorConfig
    from connectors.digital_envoy.connector import DigitalEnvoyConnector
    from connectors.digital_envoy.tools import DigitalEnvoyConnectorTools
    from connectors.digital_envoy.target import DigitalEnvoyTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = DigitalEnvoyConnectorConfig(
        api_key=digital_envoy_api_key,
        api_secret=digital_envoy_api_secret,
        base_url=digital_envoy_base_url,
        api_version=digital_envoy_api_version
    )
    assert isinstance(config, ConnectorConfig), "DigitalEnvoyConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = DigitalEnvoyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DigitalEnvoyConnector should be of type Connector"

    # get query target options
    digital_envoy_query_target_options = await connector.get_query_target_options()
    assert isinstance(digital_envoy_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select data types to target
    data_type_selector = None
    for selector in digital_envoy_query_target_options.selectors:
        if selector.type == 'data_types':  
            data_type_selector = selector
            break

    assert data_type_selector, "failed to retrieve data type selector from query target options"

    # grab geolocation data type
    assert isinstance(data_type_selector.values, list), "data_type_selector values must be a list"
    geolocation_data_type = "geolocation"  # Standard geolocation data type
    
    # Verify geolocation data type is available
    assert geolocation_data_type in data_type_selector.values, f"geolocation data type not available in data types: {data_type_selector.values}"
    
    print(f"Selecting data type: {geolocation_data_type}")

    # select intelligence feeds to target (optional)
    feed_selector = None
    for selector in digital_envoy_query_target_options.selectors:
        if selector.type == 'intelligence_feeds':  
            feed_selector = selector
            break

    intelligence_feed = None
    if feed_selector and isinstance(feed_selector.values, list) and feed_selector.values:
        intelligence_feed = feed_selector.values[0]  # Select first available feed
        print(f"Selecting intelligence feed: {intelligence_feed}")

    # set up the target with data types and intelligence feeds
    target = DigitalEnvoyTarget(data_types=[geolocation_data_type], intelligence_feeds=[intelligence_feed] if intelligence_feed else None)
    assert isinstance(target, ConnectorTargetInterface), "DigitalEnvoyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_digital_envoy_geolocation tool
    get_geolocation_tool = next(tool for tool in tools if tool.name == "get_digital_envoy_geolocation")
    
    # Test with well-known public IP addresses
    test_ip_addresses = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]  # Google DNS, Cloudflare, OpenDNS
    
    for test_ip in test_ip_addresses:
        print(f"Testing geolocation for IP: {test_ip}")
        
        geolocation_result = await get_geolocation_tool.execute(ip_address=test_ip, include_isp_info=True, accuracy_threshold=0.5)
        geolocation_data = geolocation_result.result

        print("Type of returned geolocation_data:", type(geolocation_data))
        print(f"geolocation data for {test_ip}: {str(geolocation_data)[:200]}")

        # Verify that geolocation_data is a dictionary
        assert isinstance(geolocation_data, dict), "geolocation_data should be a dictionary"
        assert len(geolocation_data) > 0, "geolocation_data should not be empty"
        
        # Verify essential Digital Envoy geolocation fields
        assert "ip_address" in geolocation_data, "Geolocation data should have an 'ip_address' field"
        assert geolocation_data["ip_address"] == test_ip, f"Returned IP {geolocation_data['ip_address']} should match requested IP {test_ip}"
        
        # Verify IP address format (basic validation)
        ip_address = geolocation_data["ip_address"]
        assert isinstance(ip_address, str), "IP address should be a string"
        assert len(ip_address.split(".")) == 4 or ":" in ip_address, "IP should be IPv4 or IPv6 format"
        
        # Check for essential location fields
        location_fields = ["country", "country_code", "region", "city"]
        for field in location_fields:
            assert field in geolocation_data, f"Geolocation data should contain '{field}' field"
        
        # Verify country code format
        if "country_code" in geolocation_data and geolocation_data["country_code"]:
            country_code = geolocation_data["country_code"]
            assert isinstance(country_code, str), "Country code should be a string"
            assert len(country_code) == 2, f"Country code should be 2 characters, got: {country_code}"
        
        # Check for coordinate information
        coordinate_fields = ["latitude", "longitude"]
        present_coordinates = [field for field in coordinate_fields if field in geolocation_data]
        print(f"IP {test_ip} contains these coordinate fields: {', '.join(present_coordinates)}")
        
        # Validate coordinates if present
        if "latitude" in geolocation_data and "longitude" in geolocation_data:
            lat = geolocation_data["latitude"]
            lon = geolocation_data["longitude"]
            if lat is not None and lon is not None:
                assert isinstance(lat, (int, float)), "Latitude should be numeric"
                assert isinstance(lon, (int, float)), "Longitude should be numeric"
                assert -90 <= lat <= 90, f"Latitude should be between -90 and 90, got: {lat}"
                assert -180 <= lon <= 180, f"Longitude should be between -180 and 180, got: {lon}"
        
        # Check for ISP and organization information
        isp_fields = ["isp", "organization", "asn", "connection_type"]
        present_isp = [field for field in isp_fields if field in geolocation_data]
        print(f"IP {test_ip} contains these ISP fields: {', '.join(present_isp)}")
        
        # Validate ASN if present
        if "asn" in geolocation_data and geolocation_data["asn"]:
            asn = geolocation_data["asn"]
            assert isinstance(asn, (int, str)), "ASN should be numeric or string"
            if isinstance(asn, str):
                # ASN might be formatted as "AS1234"
                assert asn.startswith("AS") or asn.isdigit(), f"ASN format should be valid, got: {asn}"
        
        # Check for accuracy and confidence metrics
        accuracy_fields = ["accuracy_score", "confidence_level", "data_freshness", "precision_radius"]
        present_accuracy = [field for field in accuracy_fields if field in geolocation_data]
        print(f"IP {test_ip} contains these accuracy fields: {', '.join(present_accuracy)}")
        
        # Validate accuracy score if present
        if "accuracy_score" in geolocation_data and geolocation_data["accuracy_score"] is not None:
            accuracy = geolocation_data["accuracy_score"]
            assert isinstance(accuracy, (int, float)), "Accuracy score should be numeric"
            assert 0 <= accuracy <= 1, f"Accuracy score should be between 0-1, got: {accuracy}"
        
        # Check for additional location context
        context_fields = ["timezone", "postal_code", "metro_area", "area_code"]
        present_context = [field for field in context_fields if field in geolocation_data]
        print(f"IP {test_ip} contains these context fields: {', '.join(present_context)}")
        
        # Check for network and infrastructure information
        network_fields = ["network_domain", "hosting_provider", "proxy_type", "anonymizer_status"]
        present_network = [field for field in network_fields if field in geolocation_data]
        print(f"IP {test_ip} contains these network fields: {', '.join(present_network)}")
        
        # Verify intelligence feed context if feeds were selected
        if intelligence_feed:
            feed_fields = ["intelligence_feed", "feed_timestamp", "data_source"]
            present_feed = [field for field in feed_fields if field in geolocation_data]
            if present_feed:
                print(f"IP {test_ip} contains these feed fields: {', '.join(present_feed)}")
        
        # Log the structure of the first result for debugging
        if test_ip == test_ip_addresses[0]:
            print(f"Example geolocation structure: {geolocation_data}")

        # Brief delay between requests to respect rate limiting
        import asyncio
        await asyncio.sleep(0.1)

    print(f"Successfully retrieved and validated Digital Envoy geolocation data for {len(test_ip_addresses)} IP addresses")

    return True