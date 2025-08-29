# 7-test_bulk_analysis.py

async def test_bulk_analysis(zerg_state=None):
    """Test Digital Envoy bulk IP analysis and batch processing by way of connector tools"""
    print("Attempting to authenticate using Digital Envoy connector")

    assert zerg_state, "this test requires valid zerg_state"

    digital_envoy_api_key = zerg_state.get("digital_envoy_api_key").get("value")
    digital_envoy_api_secret = zerg_state.get("digital_envoy_api_secret").get("value")
    digital_envoy_base_url = zerg_state.get("digital_envoy_base_url").get("value")
    digital_envoy_api_version = zerg_state.get("digital_envoy_api_version").get("value")

    from connectors.digital_envoy.config import DigitalEnvoyConnectorConfig
    from connectors.digital_envoy.connector import DigitalEnvoyConnector
    from connectors.digital_envoy.tools import DigitalEnvoyConnectorTools, BulkIPAnalysisInput
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

    # select multiple data types for comprehensive bulk analysis
    data_type_selector = None
    for selector in digital_envoy_query_target_options.selectors:
        if selector.type == 'data_types':  
            data_type_selector = selector
            break

    assert data_type_selector, "failed to retrieve data type selector from query target options"

    # grab multiple data types for comprehensive analysis
    assert isinstance(data_type_selector.values, list), "data_type_selector values must be a list"
    
    # Select multiple data types for bulk analysis
    desired_data_types = ["geolocation", "threat_intelligence", "demographic_intelligence"]
    available_data_types = [dt for dt in desired_data_types if dt in data_type_selector.values]
    
    assert len(available_data_types) > 0, f"No desired data types available. Available: {data_type_selector.values}"
    print(f"Selecting data types for bulk analysis: {available_data_types}")

    # select intelligence feeds to target (optional)
    feed_selector = None
    for selector in digital_envoy_query_target_options.selectors:
        if selector.type == 'intelligence_feeds':  
            feed_selector = selector
            break

    intelligence_feeds = None
    if feed_selector and isinstance(feed_selector.values, list) and feed_selector.values:
        # Select multiple feeds for comprehensive analysis
        intelligence_feeds = feed_selector.values[:2]  # Select first 2 feeds
        print(f"Selecting intelligence feeds: {intelligence_feeds}")

    # set up the target with multiple data types and intelligence feeds
    target = DigitalEnvoyTarget(data_types=available_data_types, intelligence_feeds=intelligence_feeds)
    assert isinstance(target, ConnectorTargetInterface), "DigitalEnvoyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the bulk_ip_analysis tool and execute it
    bulk_analysis_tool = next(tool for tool in tools if tool.name == "bulk_ip_analysis")
    
    # Create a comprehensive test dataset with various IP types
    test_ip_list = [
        # Public DNS servers
        "8.8.8.8", "8.8.4.4",  # Google DNS
        "1.1.1.1", "1.0.0.1",  # Cloudflare DNS
        "208.67.222.222", "208.67.220.220",  # OpenDNS
        "9.9.9.9", "149.112.112.112",  # Quad9 DNS
        # Major cloud providers
        "54.239.28.85",  # AWS
        "13.107.42.14",  # Microsoft Azure
        "35.190.247.0",  # Google Cloud
        # Content delivery networks
        "151.101.193.140",  # Reddit/Fastly
        "104.16.132.229",  # Cloudflare CDN
        # Mixed global IPs for geographic diversity
        "216.58.194.174",  # Google
        "157.240.11.35",   # Facebook
    ]
    
    print(f"Testing bulk analysis with {len(test_ip_list)} IP addresses")
    
    # Perform bulk IP analysis with comprehensive options
    bulk_result = await bulk_analysis_tool.execute(
        ip_addresses=test_ip_list,
        analysis_types=available_data_types,
        batch_size=10,
        include_confidence_scores=True,
        parallel_processing=True
    )
    bulk_analysis_data = bulk_result.result

    print("Type of returned bulk_analysis_data:", type(bulk_analysis_data))
    print(f"Bulk analysis completed for {len(test_ip_list)} IPs: {str(bulk_analysis_data)[:200]}")

    # Verify that bulk_analysis_data is a dictionary with results
    assert isinstance(bulk_analysis_data, dict), "bulk_analysis_data should be a dictionary"
    assert len(bulk_analysis_data) > 0, "bulk_analysis_data should not be empty"
    
    # Check for essential bulk analysis structure
    assert "results" in bulk_analysis_data, "Bulk analysis should have a 'results' field"
    assert "summary" in bulk_analysis_data, "Bulk analysis should have a 'summary' field"
    
    results = bulk_analysis_data["results"]
    summary = bulk_analysis_data["summary"]
    
    assert isinstance(results, (list, dict)), "Results should be a list or dictionary"
    assert isinstance(summary, dict), "Summary should be a dictionary"
    
    print(f"Bulk analysis processed {len(results)} IP results")
    
    # Verify summary statistics
    summary_fields = ["total_processed", "successful_lookups", "failed_lookups", "processing_time"]
    present_summary = [field for field in summary_fields if field in summary]
    print(f"Bulk analysis summary contains: {', '.join(present_summary)}")
    
    # Validate summary metrics
    if "total_processed" in summary:
        total_processed = summary["total_processed"]
        assert isinstance(total_processed, int), "Total processed should be an integer"
        assert total_processed == len(test_ip_list), f"Total processed {total_processed} should match input count {len(test_ip_list)}"
    
    if "successful_lookups" in summary:
        successful = summary["successful_lookups"]
        assert isinstance(successful, int), "Successful lookups should be an integer"
        assert successful <= len(test_ip_list), f"Successful lookups {successful} should not exceed total IPs"
    
    # Process individual IP results (handle both list and dict formats)
    ip_results = results if isinstance(results, list) else list(results.values())
    
    # Limit results to check for performance
    results_to_check = ip_results[:5] if len(ip_results) > 5 else ip_results
    
    # Verify structure of individual IP analysis results
    for result in results_to_check:
        assert isinstance(result, dict), "Each IP result should be a dictionary"
        
        # Verify essential fields for each IP result
        assert "ip_address" in result, "Each result should have an 'ip_address' field"
        assert "analysis_status" in result, "Each result should have an 'analysis_status' field"
        
        ip_address = result["ip_address"]
        status = result["analysis_status"]
        
        # Verify IP is from our test list
        assert ip_address in test_ip_list, f"Result IP {ip_address} should be from test list"
        
        # Verify analysis status
        valid_statuses = ["Success", "Partial", "Failed", "Timeout"]
        assert status in valid_statuses, f"Analysis status {status} should be valid"
        
        print(f"IP {ip_address} analysis status: {status}")
        
        # Check for data type specific results (only if status is Success)
        if status == "Success":
            # Check for geolocation data if requested
            if "geolocation" in available_data_types:
                geo_fields = ["geolocation_data", "country", "city", "coordinates"]
                present_geo = [field for field in geo_fields if field in result]
                print(f"IP {ip_address} geolocation fields: {', '.join(present_geo)}")
            
            # Check for threat intelligence data if requested
            if "threat_intelligence" in available_data_types:
                threat_fields = ["threat_data", "risk_score", "threat_level", "malicious_indicators"]
                present_threat = [field for field in threat_fields if field in result]
                print(f"IP {ip_address} threat fields: {', '.join(present_threat)}")
            
            # Check for demographic data if requested
            if "demographic_intelligence" in available_data_types:
                demo_fields = ["demographic_data", "market_segment", "audience_profile"]
                present_demo = [field for field in demo_fields if field in result]
                print(f"IP {ip_address} demographic fields: {', '.join(present_demo)}")
        
        # Check for confidence and quality metrics
        quality_fields = ["confidence_score", "data_quality", "processing_time", "error_details"]
        present_quality = [field for field in quality_fields if field in result]
        print(f"IP {ip_address} quality fields: {', '.join(present_quality)}")
        
        # Validate confidence score if present
        if "confidence_score" in result and result["confidence_score"] is not None:
            confidence = result["confidence_score"]
            assert isinstance(confidence, (int, float)), "Confidence score should be numeric"
            assert 0 <= confidence <= 100, f"Confidence score should be 0-100, got: {confidence}"
        
        # Check for error handling
        if status in ["Failed", "Partial"]:
            error_fields = ["error_message", "error_code", "retry_suggested"]
            present_errors = [field for field in error_fields if field in result]
            if present_errors:
                print(f"IP {ip_address} error fields: {', '.join(present_errors)}")
    
    # Check for batch processing metadata
    batch_fields = ["batch_id", "processing_method", "parallel_threads", "rate_limiting"]
    present_batch = [field for field in batch_fields if field in bulk_analysis_data]
    print(f"Bulk analysis metadata: {', '.join(present_batch)}")
    
    # Check for intelligence feed integration in bulk results
    if intelligence_feeds:
        feed_fields = ["intelligence_feeds_used", "feed_coverage", "data_sources"]
        present_feeds = [field for field in feed_fields if field in bulk_analysis_data]
        if present_feeds:
            print(f"Bulk analysis feed integration: {', '.join(present_feeds)}")
    
    # Check for performance and efficiency metrics
    performance_fields = ["requests_per_second", "cache_hit_ratio", "api_quota_usage", "optimization_applied"]
    present_performance = [field for field in performance_fields if field in bulk_analysis_data]
    print(f"Bulk analysis performance metrics: {', '.join(present_performance)}")
    
    # Validate rate limiting compliance
    if "rate_limiting" in bulk_analysis_data:
        rate_limit_info = bulk_analysis_data["rate_limiting"]
        assert isinstance(rate_limit_info, dict), "Rate limiting info should be a dictionary"
        
        rate_fields = ["requests_made", "rate_limit", "remaining_quota", "reset_time"]
        present_rate = [field for field in rate_fields if field in rate_limit_info]
        print(f"Rate limiting details: {', '.join(present_rate)}")
    
    # Check for data aggregation and insights
    aggregation_fields = ["geographic_distribution", "threat_summary", "demographic_overview"]
    present_aggregation = [field for field in aggregation_fields if field in bulk_analysis_data]
    print(f"Bulk analysis aggregations: {', '.join(present_aggregation)}")
    
    # Validate geographic distribution if present
    if "geographic_distribution" in bulk_analysis_data:
        geo_dist = bulk_analysis_data["geographic_distribution"]
        assert isinstance(geo_dist, dict), "Geographic distribution should be a dictionary"
        
        # Check for country-level aggregation
        if "countries" in geo_dist:
            countries = geo_dist["countries"]
            assert isinstance(countries, dict), "Countries should be a dictionary"
            print(f"Geographic distribution covers {len(countries)} countries")
    
    # Log overall bulk analysis structure
    print(f"Bulk analysis structure keys: {list(bulk_analysis_data.keys())}")

    print(f"Successfully completed bulk analysis of {len(test_ip_list)} IP addresses with {len(available_data_types)} data types")

    return True