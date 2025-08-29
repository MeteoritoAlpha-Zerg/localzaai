# 5-test_ip_intelligence.py

async def test_ip_intelligence(zerg_state=None):
    """Test Digital Envoy IP intelligence and threat analysis retrieval by way of connector tools"""
    print("Attempting to authenticate using Digital Envoy connector")

    assert zerg_state, "this test requires valid zerg_state"

    digital_envoy_api_key = zerg_state.get("digital_envoy_api_key").get("value")
    digital_envoy_api_secret = zerg_state.get("digital_envoy_api_secret").get("value")
    digital_envoy_base_url = zerg_state.get("digital_envoy_base_url").get("value")
    digital_envoy_api_version = zerg_state.get("digital_envoy_api_version").get("value")

    from connectors.digital_envoy.config import DigitalEnvoyConnectorConfig
    from connectors.digital_envoy.connector import DigitalEnvoyConnector
    from connectors.digital_envoy.tools import DigitalEnvoyConnectorTools, GetIPIntelligenceInput
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

    # grab threat intelligence data type
    assert isinstance(data_type_selector.values, list), "data_type_selector values must be a list"
    threat_data_type = "threat_intelligence"  # Standard threat intelligence data type
    
    # Verify threat intelligence data type is available
    assert threat_data_type in data_type_selector.values, f"threat_intelligence data type not available in data types: {data_type_selector.values}"
    
    print(f"Selecting data type: {threat_data_type}")

    # select intelligence feeds to target
    feed_selector = None
    for selector in digital_envoy_query_target_options.selectors:
        if selector.type == 'intelligence_feeds':  
            feed_selector = selector
            break

    intelligence_feed = None
    if feed_selector and isinstance(feed_selector.values, list) and feed_selector.values:
        # Look for threat-specific feeds
        threat_feeds = [feed for feed in feed_selector.values if "threat" in feed.lower() or "security" in feed.lower()]
        intelligence_feed = threat_feeds[0] if threat_feeds else feed_selector.values[0]
        print(f"Selecting intelligence feed: {intelligence_feed}")

    # set up the target with data types and intelligence feeds
    target = DigitalEnvoyTarget(data_types=[threat_data_type], intelligence_feeds=[intelligence_feed] if intelligence_feed else None)
    assert isinstance(target, ConnectorTargetInterface), "DigitalEnvoyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_digital_envoy_ip_intelligence tool and execute it
    get_ip_intelligence_tool = next(tool for tool in tools if tool.name == "get_digital_envoy_ip_intelligence")
    
    # Test with a mix of IP addresses for comprehensive intelligence analysis
    test_ip_addresses = ["8.8.8.8", "192.168.1.1", "10.0.0.1"]  # Public, private, and reserved IPs
    
    for test_ip in test_ip_addresses:
        print(f"Testing IP intelligence for IP: {test_ip}")
        
        # Get IP intelligence with threat analysis and risk scoring
        intelligence_result = await get_ip_intelligence_tool.execute(
            ip_address=test_ip, 
            include_threat_analysis=True, 
            include_risk_scoring=True,
            threat_lookback_days=30
        )
        ip_intelligence_data = intelligence_result.result

        print("Type of returned ip_intelligence_data:", type(ip_intelligence_data))
        print(f"IP intelligence data for {test_ip}: {str(ip_intelligence_data)[:200]}")

        # Verify that ip_intelligence_data is a dictionary
        assert isinstance(ip_intelligence_data, dict), "ip_intelligence_data should be a dictionary"
        assert len(ip_intelligence_data) > 0, "ip_intelligence_data should not be empty"
        
        # Verify essential Digital Envoy IP intelligence fields
        assert "ip_address" in ip_intelligence_data, "IP intelligence data should have an 'ip_address' field"
        assert ip_intelligence_data["ip_address"] == test_ip, f"Returned IP {ip_intelligence_data['ip_address']} should match requested IP {test_ip}"
        
        # Check for threat classification and risk assessment
        threat_fields = ["threat_classification", "risk_score", "threat_level", "malicious_activity"]
        present_threat = [field for field in threat_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these threat fields: {', '.join(present_threat)}")
        
        # Validate risk score if present
        if "risk_score" in ip_intelligence_data and ip_intelligence_data["risk_score"] is not None:
            risk_score = ip_intelligence_data["risk_score"]
            assert isinstance(risk_score, (int, float)), "Risk score should be numeric"
            assert 0 <= risk_score <= 100, f"Risk score should be between 0-100, got: {risk_score}"
        
        # Validate threat level if present
        if "threat_level" in ip_intelligence_data and ip_intelligence_data["threat_level"]:
            threat_level = ip_intelligence_data["threat_level"]
            valid_threat_levels = ["Low", "Medium", "High", "Critical", "Unknown", "Clean"]
            assert threat_level in valid_threat_levels, f"Threat level {threat_level} should be one of {valid_threat_levels}"
        
        # Check for malicious activity indicators
        malicious_fields = ["malware_detected", "botnet_activity", "spam_source", "phishing_detected", "blacklist_status"]
        present_malicious = [field for field in malicious_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these malicious activity fields: {', '.join(present_malicious)}")
        
        # Validate blacklist status if present
        if "blacklist_status" in ip_intelligence_data:
            blacklist_status = ip_intelligence_data["blacklist_status"]
            assert isinstance(blacklist_status, (bool, str, list)), "Blacklist status should be boolean, string, or list"
        
        # Check for threat intelligence sources and attribution
        attribution_fields = ["threat_actors", "attack_campaigns", "malware_families", "ioc_indicators"]
        present_attribution = [field for field in attribution_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these attribution fields: {', '.join(present_attribution)}")
        
        # Check for network reputation and behavior analysis
        reputation_fields = ["reputation_score", "behavioral_analysis", "traffic_patterns", "anomaly_detection"]
        present_reputation = [field for field in reputation_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these reputation fields: {', '.join(present_reputation)}")
        
        # Validate reputation score if present
        if "reputation_score" in ip_intelligence_data and ip_intelligence_data["reputation_score"] is not None:
            reputation = ip_intelligence_data["reputation_score"]
            assert isinstance(reputation, (int, float)), "Reputation score should be numeric"
            assert 0 <= reputation <= 100, f"Reputation score should be between 0-100, got: {reputation}"
        
        # Check for temporal and historical analysis
        temporal_fields = ["first_seen", "last_seen", "activity_timeline", "historical_threats"]
        present_temporal = [field for field in temporal_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these temporal fields: {', '.join(present_temporal)}")
        
        # Check for geographic and network context
        context_fields = ["geographic_risk", "network_infrastructure", "hosting_analysis", "proxy_detection"]
        present_context = [field for field in context_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these context fields: {', '.join(present_context)}")
        
        # Validate proxy detection if present
        if "proxy_detection" in ip_intelligence_data:
            proxy_detection = ip_intelligence_data["proxy_detection"]
            assert isinstance(proxy_detection, dict), "Proxy detection should be a dictionary"
            
            proxy_fields = ["is_proxy", "proxy_type", "anonymization_level"]
            present_proxy = [field for field in proxy_fields if field in proxy_detection]
            print(f"Proxy detection contains: {', '.join(present_proxy)}")
        
        # Check for threat intelligence feed context
        if intelligence_feed:
            feed_fields = ["intelligence_feed", "feed_confidence", "data_freshness", "source_reliability"]
            present_feed = [field for field in feed_fields if field in ip_intelligence_data]
            if present_feed:
                print(f"IP {test_ip} contains these feed fields: {', '.join(present_feed)}")
                
                # Validate feed confidence if present
                if "feed_confidence" in ip_intelligence_data and ip_intelligence_data["feed_confidence"] is not None:
                    confidence = ip_intelligence_data["feed_confidence"]
                    assert isinstance(confidence, (int, float)), "Feed confidence should be numeric"
                    assert 0 <= confidence <= 100, f"Feed confidence should be between 0-100, got: {confidence}"
        
        # Check for security recommendations and mitigation
        security_fields = ["security_recommendations", "mitigation_strategies", "blocking_advisories", "monitoring_suggestions"]
        present_security = [field for field in security_fields if field in ip_intelligence_data]
        print(f"IP {test_ip} contains these security fields: {', '.join(present_security)}")
        
        # Check for compliance and regulatory context
        compliance_fields = ["regulatory_flags", "compliance_violations", "data_privacy_concerns"]
        present_compliance = [field for field in compliance_fields if field in ip_intelligence_data]
        if present_compliance:
            print(f"IP {test_ip} contains these compliance fields: {', '.join(present_compliance)}")
        
        # Log the structure of the first result for debugging
        if test_ip == test_ip_addresses[0]:
            print(f"Example IP intelligence structure: {ip_intelligence_data}")

        # Brief delay between requests to respect rate limiting
        import asyncio
        await asyncio.sleep(0.1)

    print(f"Successfully retrieved and validated Digital Envoy IP intelligence data for {len(test_ip_addresses)} IP addresses")

    return True