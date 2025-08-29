# 6-test_demographic_intelligence.py

async def test_demographic_intelligence(zerg_state=None):
    """Test Digital Envoy demographic and business intelligence retrieval by way of connector tools"""
    print("Attempting to authenticate using Digital Envoy connector")

    assert zerg_state, "this test requires valid zerg_state"

    digital_envoy_api_key = zerg_state.get("digital_envoy_api_key").get("value")
    digital_envoy_api_secret = zerg_state.get("digital_envoy_api_secret").get("value")
    digital_envoy_base_url = zerg_state.get("digital_envoy_base_url").get("value")
    digital_envoy_api_version = zerg_state.get("digital_envoy_api_version").get("value")

    from connectors.digital_envoy.config import DigitalEnvoyConnectorConfig
    from connectors.digital_envoy.connector import DigitalEnvoyConnector
    from connectors.digital_envoy.tools import DigitalEnvoyConnectorTools, GetDemographicIntelligenceInput
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

    # grab demographic intelligence data type
    assert isinstance(data_type_selector.values, list), "data_type_selector values must be a list"
    demographic_data_type = "demographic_intelligence"  # Standard demographic intelligence data type
    
    # Verify demographic intelligence data type is available
    assert demographic_data_type in data_type_selector.values, f"demographic_intelligence data type not available in data types: {data_type_selector.values}"
    
    print(f"Selecting data type: {demographic_data_type}")

    # select intelligence feeds to target
    feed_selector = None
    for selector in digital_envoy_query_target_options.selectors:
        if selector.type == 'intelligence_feeds':  
            feed_selector = selector
            break

    intelligence_feed = None
    if feed_selector and isinstance(feed_selector.values, list) and feed_selector.values:
        # Look for demographic or business intelligence feeds
        demo_feeds = [feed for feed in feed_selector.values if "demographic" in feed.lower() or "business" in feed.lower() or "market" in feed.lower()]
        intelligence_feed = demo_feeds[0] if demo_feeds else feed_selector.values[0]
        print(f"Selecting intelligence feed: {intelligence_feed}")

    # set up the target with data types and intelligence feeds
    target = DigitalEnvoyTarget(data_types=[demographic_data_type], intelligence_feeds=[intelligence_feed] if intelligence_feed else None)
    assert isinstance(target, ConnectorTargetInterface), "DigitalEnvoyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_digital_envoy_demographic_intelligence tool and execute it
    get_demographic_intelligence_tool = next(tool for tool in tools if tool.name == "get_digital_envoy_demographic_intelligence")
    
    # Test with IP addresses from different geographic regions for diverse demographic data
    test_ip_addresses = ["8.8.8.8", "208.67.222.222", "9.9.9.9"]  # Google DNS, OpenDNS, Quad9
    
    for test_ip in test_ip_addresses:
        print(f"Testing demographic intelligence for IP: {test_ip}")
        
        # Get demographic intelligence with business and market analysis
        demographic_result = await get_demographic_intelligence_tool.execute(
            ip_address=test_ip, 
            include_business_intelligence=True, 
            include_market_segmentation=True,
            demographic_categories=["age", "income", "education", "lifestyle"]
        )
        demographic_data = demographic_result.result

        print("Type of returned demographic_data:", type(demographic_data))
        print(f"Demographic data for {test_ip}: {str(demographic_data)[:200]}")

        # Verify that demographic_data is a dictionary
        assert isinstance(demographic_data, dict), "demographic_data should be a dictionary"
        assert len(demographic_data) > 0, "demographic_data should not be empty"
        
        # Verify essential Digital Envoy demographic intelligence fields
        assert "ip_address" in demographic_data, "Demographic data should have an 'ip_address' field"
        assert demographic_data["ip_address"] == test_ip, f"Returned IP {demographic_data['ip_address']} should match requested IP {test_ip}"
        
        # Check for geographic demographic context
        geographic_fields = ["geographic_segment", "market_region", "population_density", "urbanization_level"]
        present_geographic = [field for field in geographic_fields if field in demographic_data]
        print(f"IP {test_ip} contains these geographic fields: {', '.join(present_geographic)}")
        
        # Validate population density if present
        if "population_density" in demographic_data and demographic_data["population_density"] is not None:
            pop_density = demographic_data["population_density"]
            valid_densities = ["Urban", "Suburban", "Rural", "Metropolitan", "Unknown"]
            assert pop_density in valid_densities, f"Population density {pop_density} should be one of {valid_densities}"
        
        # Check for demographic profile and segmentation
        demographic_fields = ["age_distribution", "income_brackets", "education_levels", "household_composition"]
        present_demographic = [field for field in demographic_fields if field in demographic_data]
        print(f"IP {test_ip} contains these demographic fields: {', '.join(present_demographic)}")
        
        # Validate age distribution if present
        if "age_distribution" in demographic_data and demographic_data["age_distribution"]:
            age_dist = demographic_data["age_distribution"]
            assert isinstance(age_dist, dict), "Age distribution should be a dictionary"
            
            # Check for standard age brackets
            age_brackets = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
            for bracket in age_brackets:
                if bracket in age_dist:
                    percentage = age_dist[bracket]
                    if percentage is not None:
                        assert isinstance(percentage, (int, float)), f"Age bracket {bracket} should be numeric"
                        assert 0 <= percentage <= 100, f"Age percentage should be 0-100, got: {percentage}"
        
        # Check for income and economic indicators
        economic_fields = ["income_median", "income_distribution", "spending_power", "economic_segment"]
        present_economic = [field for field in economic_fields if field in demographic_data]
        print(f"IP {test_ip} contains these economic fields: {', '.join(present_economic)}")
        
        # Validate income distribution if present
        if "income_distribution" in demographic_data and demographic_data["income_distribution"]:
            income_dist = demographic_data["income_distribution"]
            assert isinstance(income_dist, dict), "Income distribution should be a dictionary"
            
            # Check for standard income brackets
            income_brackets = ["<25k", "25k-50k", "50k-75k", "75k-100k", "100k-150k", "150k+"]
            for bracket in income_brackets:
                if bracket in income_dist:
                    percentage = income_dist[bracket]
                    if percentage is not None:
                        assert isinstance(percentage, (int, float)), f"Income bracket {bracket} should be numeric"
                        assert 0 <= percentage <= 100, f"Income percentage should be 0-100, got: {percentage}"
        
        # Check for lifestyle and behavioral segmentation
        lifestyle_fields = ["lifestyle_segments", "interests", "purchasing_behavior", "digital_engagement"]
        present_lifestyle = [field for field in lifestyle_fields if field in demographic_data]
        print(f"IP {test_ip} contains these lifestyle fields: {', '.join(present_lifestyle)}")
        
        # Check for business and commercial intelligence
        business_fields = ["business_segment", "industry_presence", "commercial_activity", "b2b_indicators"]
        present_business = [field for field in business_fields if field in demographic_data]
        print(f"IP {test_ip} contains these business fields: {', '.join(present_business)}")
        
        # Validate business segment if present
        if "business_segment" in demographic_data and demographic_data["business_segment"]:
            business_segment = demographic_data["business_segment"]
            valid_segments = ["Enterprise", "SMB", "Residential", "Educational", "Government", "Healthcare", "Unknown"]
            assert business_segment in valid_segments, f"Business segment {business_segment} should be one of {valid_segments}"
        
        # Check for market segmentation and targeting
        market_fields = ["market_segments", "consumer_profiles", "target_audiences", "market_penetration"]
        present_market = [field for field in market_fields if field in demographic_data]
        print(f"IP {test_ip} contains these market fields: {', '.join(present_market)}")
        
        # Check for technology and digital behavior
        tech_fields = ["technology_adoption", "device_preferences", "internet_usage", "digital_literacy"]
        present_tech = [field for field in tech_fields if field in demographic_data]
        print(f"IP {test_ip} contains these technology fields: {', '.join(present_tech)}")
        
        # Validate technology adoption if present
        if "technology_adoption" in demographic_data and demographic_data["technology_adoption"]:
            tech_adoption = demographic_data["technology_adoption"]
            assert isinstance(tech_adoption, dict), "Technology adoption should be a dictionary"
            
            tech_categories = ["mobile", "broadband", "social_media", "e_commerce"]
            for category in tech_categories:
                if category in tech_adoption:
                    adoption_rate = tech_adoption[category]
                    if adoption_rate is not None:
                        assert isinstance(adoption_rate, (int, float)), f"Tech adoption {category} should be numeric"
                        assert 0 <= adoption_rate <= 100, f"Adoption rate should be 0-100, got: {adoption_rate}"
        
        # Check for confidence and accuracy metrics
        confidence_fields = ["confidence_score", "data_accuracy", "sample_size", "data_freshness"]
        present_confidence = [field for field in confidence_fields if field in demographic_data]
        print(f"IP {test_ip} contains these confidence fields: {', '.join(present_confidence)}")
        
        # Validate confidence score if present
        if "confidence_score" in demographic_data and demographic_data["confidence_score"] is not None:
            confidence = demographic_data["confidence_score"]
            assert isinstance(confidence, (int, float)), "Confidence score should be numeric"
            assert 0 <= confidence <= 100, f"Confidence score should be between 0-100, got: {confidence}"
        
        # Check for temporal and trend analysis
        trend_fields = ["demographic_trends", "seasonal_patterns", "growth_indicators", "migration_patterns"]
        present_trends = [field for field in trend_fields if field in demographic_data]
        print(f"IP {test_ip} contains these trend fields: {', '.join(present_trends)}")
        
        # Check for intelligence feed context
        if intelligence_feed:
            feed_fields = ["intelligence_feed", "data_source", "collection_method", "update_frequency"]
            present_feed = [field for field in feed_fields if field in demographic_data]
            if present_feed:
                print(f"IP {test_ip} contains these feed fields: {', '.join(present_feed)}")
        
        # Check for privacy and compliance considerations
        privacy_fields = ["privacy_compliance", "data_anonymization", "consent_status", "opt_out_flags"]
        present_privacy = [field for field in privacy_fields if field in demographic_data]
        if present_privacy:
            print(f"IP {test_ip} contains these privacy fields: {', '.join(present_privacy)}")
        
        # Check for audience analytics and insights
        audience_fields = ["audience_size", "reach_potential", "engagement_metrics", "conversion_indicators"]
        present_audience = [field for field in audience_fields if field in demographic_data]
        print(f"IP {test_ip} contains these audience fields: {', '.join(present_audience)}")
        
        # Validate audience size if present
        if "audience_size" in demographic_data and demographic_data["audience_size"] is not None:
            audience_size = demographic_data["audience_size"]
            assert isinstance(audience_size, (int, str)), "Audience size should be numeric or descriptive"
            if isinstance(audience_size, str):
                valid_sizes = ["Small", "Medium", "Large", "Very Large", "Unknown"]
                assert audience_size in valid_sizes, f"Audience size {audience_size} should be valid"
        
        # Log the structure of the first result for debugging
        if test_ip == test_ip_addresses[0]:
            print(f"Example demographic intelligence structure: {demographic_data}")

        # Brief delay between requests to respect rate limiting
        import asyncio
        await asyncio.sleep(0.1)

    print(f"Successfully retrieved and validated Digital Envoy demographic intelligence data for {len(test_ip_addresses)} IP addresses")

    return True