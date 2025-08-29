# 6-test_threat_feeds.py

async def test_threat_feeds(zerg_state=None):
    """Test Infoblox network security analytics and threat feeds retrieval"""
    print("Attempting to retrieve threat feeds using Infoblox connector")

    assert zerg_state, "this test requires valid zerg_state"

    infoblox_url = zerg_state.get("infoblox_url").get("value")
    infoblox_username = zerg_state.get("infoblox_username").get("value")
    infoblox_password = zerg_state.get("infoblox_password").get("value")
    infoblox_wapi_version = zerg_state.get("infoblox_wapi_version").get("value")

    from connectors.infoblox.config import InfobloxConnectorConfig
    from connectors.infoblox.connector import InfobloxConnector
    from connectors.infoblox.tools import InfobloxConnectorTools
    from connectors.infoblox.target import InfobloxTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = InfobloxConnectorConfig(
        url=infoblox_url,
        username=infoblox_username,
        password=infoblox_password,
        wapi_version=infoblox_wapi_version,
    )
    assert isinstance(config, ConnectorConfig), "InfobloxConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = InfobloxConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "InfobloxConnector should be of type Connector"

    # get query target options
    infoblox_query_target_options = await connector.get_query_target_options()
    assert isinstance(infoblox_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select networks to target
    network_selector = None
    for selector in infoblox_query_target_options.selectors:
        if selector.type == 'network_refs':  
            network_selector = selector
            break

    assert network_selector, "failed to retrieve network selector from query target options"

    assert isinstance(network_selector.values, list), "network_selector values must be a list"
    network_ref = network_selector.values[0] if network_selector.values else None
    print(f"Selecting network ref: {network_ref}")

    assert network_ref, f"failed to retrieve network ref from network selector"

    # set up the target with network refs
    target = InfobloxTarget(network_refs=[network_ref])
    assert isinstance(target, ConnectorTargetInterface), "InfobloxTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get threat intelligence feeds
    get_infoblox_threat_feeds_tool = next(tool for tool in tools if tool.name == "get_infoblox_threat_feeds")
    infoblox_threat_feeds_result = await get_infoblox_threat_feeds_tool.execute(
        limit=20  # limit to 20 feeds for testing
    )
    infoblox_threat_feeds = infoblox_threat_feeds_result.result

    print("Type of returned infoblox_threat_feeds:", type(infoblox_threat_feeds))
    print(f"len threat feeds: {len(infoblox_threat_feeds)} feeds: {str(infoblox_threat_feeds)[:200]}")

    # Verify that infoblox_threat_feeds is a list
    assert isinstance(infoblox_threat_feeds, list), "infoblox_threat_feeds should be a list"
    
    # Threat feeds might be empty, which is acceptable
    if len(infoblox_threat_feeds) > 0:
        # Limit the number of feeds to check if there are many
        feeds_to_check = infoblox_threat_feeds[:5] if len(infoblox_threat_feeds) > 5 else infoblox_threat_feeds
        
        # Verify structure of each threat feed object
        for feed in feeds_to_check:
            # Verify essential Infoblox threat feed fields
            assert "_ref" in feed, "Each threat feed should have a '_ref' field"
            assert "name" in feed, "Each threat feed should have a 'name' field"
            assert "feed_type" in feed, "Each threat feed should have a 'feed_type' field"
            
            # Verify common threat feed fields
            assert "enabled" in feed, "Each threat feed should have an 'enabled' field"
            
            # Check for common feed types
            valid_feed_types = ["domain", "ip", "url", "hash", "custom"]
            assert feed["feed_type"] in valid_feed_types, f"Feed type {feed['feed_type']} is not a recognized type"
            
            # Check for additional optional fields
            optional_fields = ["description", "source", "last_updated", "update_frequency", "confidence", "category"]
            present_optional = [field for field in optional_fields if field in feed]
            
            print(f"Threat feed {feed['name']} ({feed['feed_type']}) contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first feed for debugging
            if feed == feeds_to_check[0]:
                print(f"Example threat feed structure: {feed}")

        print(f"Successfully retrieved and validated {len(infoblox_threat_feeds)} Infoblox threat feeds")
    else:
        print("No threat feeds found - this is acceptable for testing")

    # Test 2: Get network security analytics
    get_infoblox_network_analytics_tool = next(tool for tool in tools if tool.name == "get_infoblox_network_analytics")
    infoblox_network_analytics_result = await get_infoblox_network_analytics_tool.execute(
        network_ref=network_ref,
        limit=25  # limit to 25 analytics records for testing
    )
    infoblox_network_analytics = infoblox_network_analytics_result.result

    print("Type of returned infoblox_network_analytics:", type(infoblox_network_analytics))
    print(f"len network analytics: {len(infoblox_network_analytics)} analytics: {str(infoblox_network_analytics)[:200]}")

    # Verify that infoblox_network_analytics is a list
    assert isinstance(infoblox_network_analytics, list), "infoblox_network_analytics should be a list"
    
    # Network analytics might be empty, which is acceptable
    if len(infoblox_network_analytics) > 0:
        # Limit the number of analytics to check
        analytics_to_check = infoblox_network_analytics[:3] if len(infoblox_network_analytics) > 3 else infoblox_network_analytics
        
        # Verify structure of each network analytics object
        for analytics in analytics_to_check:
            # Verify essential Infoblox network analytics fields
            assert "timestamp" in analytics, "Each network analytics record should have a 'timestamp' field"
            assert "source_ip" in analytics, "Each network analytics record should have a 'source_ip' field"
            assert "destination_ip" in analytics, "Each network analytics record should have a 'destination_ip' field"
            
            # Verify common network analytics fields
            assert "traffic_type" in analytics, "Each network analytics record should have a 'traffic_type' field"
            assert "bytes_transferred" in analytics, "Each network analytics record should have a 'bytes_transferred' field"
            
            # Check for common traffic types
            valid_traffic_types = ["dns", "http", "https", "tcp", "udp", "icmp"]
            
            # Check for additional optional fields
            optional_fields = ["port", "protocol", "duration", "packets", "anomaly_score", "threat_indicator"]
            present_optional = [field for field in optional_fields if field in analytics]
            
            print(f"Network analytics {analytics['source_ip']} -> {analytics['destination_ip']} contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first analytics record for debugging
            if analytics == analytics_to_check[0]:
                print(f"Example network analytics structure: {analytics}")

        print(f"Successfully retrieved and validated {len(infoblox_network_analytics)} Infoblox network analytics records")
    else:
        print("No network analytics found - this is acceptable for testing")

    # Test 3: Get BloxOne threat defense data
    get_infoblox_bloxone_threat_tool = next(tool for tool in tools if tool.name == "get_infoblox_bloxone_threat")
    infoblox_bloxone_threat_result = await get_infoblox_bloxone_threat_tool.execute(
        limit=15  # limit to 15 BloxOne threat records for testing
    )
    infoblox_bloxone_threat = infoblox_bloxone_threat_result.result

    print("Type of returned infoblox_bloxone_threat:", type(infoblox_bloxone_threat))
    print(f"len BloxOne threat records: {len(infoblox_bloxone_threat)} records: {str(infoblox_bloxone_threat)[:200]}")

    # Verify that infoblox_bloxone_threat is a list
    assert isinstance(infoblox_bloxone_threat, list), "infoblox_bloxone_threat should be a list"
    
    # BloxOne threat data might be empty, which is acceptable
    if len(infoblox_bloxone_threat) > 0:
        # Check structure of BloxOne threat records
        threat_to_check = infoblox_bloxone_threat[:3] if len(infoblox_bloxone_threat) > 3 else infoblox_bloxone_threat
        
        for threat in threat_to_check:
            assert "id" in threat, "Each BloxOne threat record should have an 'id' field"
            assert "threat_type" in threat, "Each BloxOne threat record should have a 'threat_type' field"
            assert "detected_at" in threat, "Each BloxOne threat record should have a 'detected_at' field"
            
            # Check for additional BloxOne fields
            bloxone_fields = ["severity", "confidence", "source_ip", "destination", "policy_action", "category"]
            present_bloxone_fields = [field for field in bloxone_fields if field in threat]
            
            print(f"BloxOne threat {threat['id']} ({threat['threat_type']}) contains these fields: {', '.join(present_bloxone_fields)}")

        print(f"Successfully retrieved and validated {len(infoblox_bloxone_threat)} Infoblox BloxOne threat records")
    else:
        print("No BloxOne threat records found - this is acceptable for testing")

    # Test 4: Get DNS reputation data
    get_infoblox_dns_reputation_tool = next(tool for tool in tools if tool.name == "get_infoblox_dns_reputation")
    
    # Use a test domain for reputation lookup
    test_domain = "example.com"
    
    infoblox_dns_reputation_result = await get_infoblox_dns_reputation_tool.execute(
        domain=test_domain
    )
    infoblox_dns_reputation = infoblox_dns_reputation_result.result

    print("Type of returned infoblox_dns_reputation:", type(infoblox_dns_reputation))
    
    # Verify DNS reputation structure
    assert isinstance(infoblox_dns_reputation, dict), "infoblox_dns_reputation should be a dictionary"
    
    # DNS reputation might be empty for unknown domains, which is acceptable
    if infoblox_dns_reputation:
        assert "domain" in infoblox_dns_reputation, "DNS reputation should contain domain field"
        assert "reputation_score" in infoblox_dns_reputation, "DNS reputation should contain reputation_score field"
        
        print(f"DNS reputation for {test_domain}: {infoblox_dns_reputation}")

    print("Successfully completed threat feeds and network security analytics tests")

    return True