# 8-test_historical_analysis.py

async def test_historical_analysis(zerg_state=None):
    """Test Digital Envoy historical and trend analysis retrieval by way of connector tools"""
    print("Attempting to authenticate using Digital Envoy connector")

    assert zerg_state, "this test requires valid zerg_state"

    digital_envoy_api_key = zerg_state.get("digital_envoy_api_key").get("value")
    digital_envoy_api_secret = zerg_state.get("digital_envoy_api_secret").get("value")
    digital_envoy_base_url = zerg_state.get("digital_envoy_base_url").get("value")
    digital_envoy_api_version = zerg_state.get("digital_envoy_api_version").get("value")

    from connectors.digital_envoy.config import DigitalEnvoyConnectorConfig
    from connectors.digital_envoy.connector import DigitalEnvoyConnector
    from connectors.digital_envoy.tools import DigitalEnvoyConnectorTools, GetHistoricalAnalysisInput
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

    # select data types for historical analysis
    data_type_selector = None
    for selector in digital_envoy_query_target_options.selectors:
        if selector.type == 'data_types':  
            data_type_selector = selector
            break

    assert data_type_selector, "failed to retrieve data type selector from query target options"

    # grab multiple data types for comprehensive historical analysis
    assert isinstance(data_type_selector.values, list), "data_type_selector values must be a list"
    
    # Select data types that support historical analysis
    desired_data_types = ["geolocation", "threat_intelligence", "demographic_intelligence"]
    available_data_types = [dt for dt in desired_data_types if dt in data_type_selector.values]
    
    assert len(available_data_types) > 0, f"No desired data types available. Available: {data_type_selector.values}"
    print(f"Selecting data types for historical analysis: {available_data_types}")

    # select intelligence feeds that support historical data
    feed_selector = None
    for selector in digital_envoy_query_target_options.selectors:
        if selector.type == 'intelligence_feeds':  
            feed_selector = selector
            break

    intelligence_feeds = None
    if feed_selector and isinstance(feed_selector.values, list) and feed_selector.values:
        # Look for feeds that support historical data
        historical_feeds = [feed for feed in feed_selector.values if "historical" in feed.lower() or "trend" in feed.lower()]
        intelligence_feeds = historical_feeds if historical_feeds else feed_selector.values[:1]
        print(f"Selecting intelligence feeds for historical analysis: {intelligence_feeds}")

    # set up the target with data types and intelligence feeds
    target = DigitalEnvoyTarget(data_types=available_data_types, intelligence_feeds=intelligence_feeds)
    assert isinstance(target, ConnectorTargetInterface), "DigitalEnvoyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_digital_envoy_historical_analysis tool and execute it
    get_historical_analysis_tool = next(tool for tool in tools if tool.name == "get_digital_envoy_historical_analysis")
    
    # Test with IP addresses that likely have rich historical data
    test_scenarios = [
        {
            "ip_address": "8.8.8.8",
            "description": "Google DNS - stable infrastructure",
            "time_range": "1year"
        },
        {
            "ip_address": "1.1.1.1", 
            "description": "Cloudflare DNS - newer service with growth patterns",
            "time_range": "6months"
        },
        {
            "ip_address": "208.67.222.222",
            "description": "OpenDNS - established service with historical data",
            "time_range": "2years"
        }
    ]
    
    for scenario in test_scenarios:
        ip_address = scenario["ip_address"]
        time_range = scenario["time_range"]
        description = scenario["description"]
        
        print(f"Testing historical analysis for {ip_address} ({description}) over {time_range}")
        
        # Get historical analysis with comprehensive temporal data
        historical_result = await get_historical_analysis_tool.execute(
            ip_address=ip_address,
            time_range=time_range,
            analysis_types=available_data_types,
            include_trend_analysis=True,
            granularity="monthly",
            include_anomalies=True
        )
        historical_data = historical_result.result

        print("Type of returned historical_data:", type(historical_data))
        print(f"Historical data for {ip_address}: {str(historical_data)[:200]}")

        # Verify that historical_data is a dictionary
        assert isinstance(historical_data, dict), "historical_data should be a dictionary"
        assert len(historical_data) > 0, "historical_data should not be empty"
        
        # Verify essential Digital Envoy historical analysis fields
        assert "ip_address" in historical_data, "Historical data should have an 'ip_address' field"
        assert historical_data["ip_address"] == ip_address, f"Returned IP {historical_data['ip_address']} should match requested IP {ip_address}"
        
        # Check for temporal scope and metadata
        temporal_fields = ["time_range", "analysis_period", "data_points", "granularity"]
        present_temporal = [field for field in temporal_fields if field in historical_data]
        print(f"IP {ip_address} temporal fields: {', '.join(present_temporal)}")
        
        # Validate time range if present
        if "time_range" in historical_data:
            returned_range = historical_data["time_range"]
            assert isinstance(returned_range, (str, dict)), "Time range should be string or dictionary"
        
        # Check for historical timeline and data points
        assert "timeline" in historical_data, "Historical data should have a 'timeline' field"
        timeline = historical_data["timeline"]
        assert isinstance(timeline, list), "Timeline should be a list of temporal data points"
        assert len(timeline) > 0, "Timeline should contain data points"
        
        print(f"IP {ip_address} timeline contains {len(timeline)} data points")
        
        # Validate timeline data points
        timeline_to_check = timeline[:3] if len(timeline) > 3 else timeline
        for data_point in timeline_to_check:
            assert isinstance(data_point, dict), "Each timeline point should be a dictionary"
            
            # Essential temporal fields
            point_fields = ["timestamp", "date", "data_snapshot"]
            present_point_fields = [field for field in point_fields if field in data_point]
            assert len(present_point_fields) > 0, "Timeline point should have temporal identifiers"
            
            # Validate data snapshot if present
            if "data_snapshot" in data_point:
                snapshot = data_point["data_snapshot"]
                assert isinstance(snapshot, dict), "Data snapshot should be a dictionary"
        
        # Check for geolocation historical trends if requested
        if "geolocation" in available_data_types:
            geo_trend_fields = ["geolocation_history", "location_changes", "geographic_migration"]
            present_geo_trends = [field for field in geo_trend_fields if field in historical_data]
            print(f"IP {ip_address} geolocation trend fields: {', '.join(present_geo_trends)}")
            
            # Validate location changes if present
            if "location_changes" in historical_data:
                location_changes = historical_data["location_changes"]
                assert isinstance(location_changes, list), "Location changes should be a list"
                
                for change in location_changes[:2]:  # Check first 2 changes
                    change_fields = ["change_date", "previous_location", "new_location", "confidence"]
                    present_change_fields = [field for field in change_fields if field in change]
                    print(f"Location change contains: {', '.join(present_change_fields)}")
        
        # Check for threat intelligence historical trends if requested
        if "threat_intelligence" in available_data_types:
            threat_trend_fields = ["threat_history", "risk_evolution", "security_incidents", "threat_timeline"]
            present_threat_trends = [field for field in threat_trend_fields if field in historical_data]
            print(f"IP {ip_address} threat trend fields: {', '.join(present_threat_trends)}")
            
            # Validate threat history if present
            if "threat_history" in historical_data:
                threat_history = historical_data["threat_history"]
                assert isinstance(threat_history, list), "Threat history should be a list"
                
                for incident in threat_history[:2]:  # Check first 2 incidents
                    incident_fields = ["incident_date", "threat_type", "severity", "resolution_status"]
                    present_incident_fields = [field for field in incident_fields if field in incident]
                    print(f"Threat incident contains: {', '.join(present_incident_fields)}")
        
        # Check for demographic historical trends if requested
        if "demographic_intelligence" in available_data_types:
            demo_trend_fields = ["demographic_evolution", "population_changes", "market_shifts", "behavioral_trends"]
            present_demo_trends = [field for field in demo_trend_fields if field in historical_data]
            print(f"IP {ip_address} demographic trend fields: {', '.join(present_demo_trends)}")
            
            # Validate demographic evolution if present
            if "demographic_evolution" in historical_data:
                demo_evolution = historical_data["demographic_evolution"]
                assert isinstance(demo_evolution, dict), "Demographic evolution should be a dictionary"
                
                evolution_fields = ["age_distribution_changes", "income_shifts", "lifestyle_trends"]
                present_evolution = [field for field in evolution_fields if field in demo_evolution]
                print(f"Demographic evolution contains: {', '.join(present_evolution)}")
        
        # Check for trend analysis and patterns
        trend_fields = ["trend_analysis", "patterns", "seasonality", "growth_indicators"]
        present_trends = [field for field in trend_fields if field in historical_data]
        print(f"IP {ip_address} trend analysis fields: {', '.join(present_trends)}")
        
        # Validate trend analysis if present
        if "trend_analysis" in historical_data:
            trend_analysis = historical_data["trend_analysis"]
            assert isinstance(trend_analysis, dict), "Trend analysis should be a dictionary"
            
            # Check for statistical trend metrics
            trend_metrics = ["trend_direction", "change_rate", "volatility", "correlation_factors"]
            present_metrics = [field for field in trend_metrics if field in trend_analysis]
            print(f"Trend analysis contains: {', '.join(present_metrics)}")
            
            # Validate trend direction if present
            if "trend_direction" in trend_analysis:
                direction = trend_analysis["trend_direction"]
                valid_directions = ["Increasing", "Decreasing", "Stable", "Volatile", "Unknown"]
                assert direction in valid_directions, f"Trend direction {direction} should be valid"
        
        # Check for anomaly detection and outliers
        anomaly_fields = ["anomalies", "outliers", "unusual_patterns", "deviation_analysis"]
        present_anomalies = [field for field in anomaly_fields if field in historical_data]
        print(f"IP {ip_address} anomaly fields: {', '.join(present_anomalies)}")
        
        # Validate anomalies if present
        if "anomalies" in historical_data:
            anomalies = historical_data["anomalies"]
            assert isinstance(anomalies, list), "Anomalies should be a list"
            
            for anomaly in anomalies[:2]:  # Check first 2 anomalies
                anomaly_fields = ["anomaly_date", "anomaly_type", "severity", "description"]
                present_anomaly_fields = [field for field in anomaly_fields if field in anomaly]
                print(f"Anomaly contains: {', '.join(present_anomaly_fields)}")
        
        # Check for predictive analysis and forecasting
        predictive_fields = ["forecasts", "predictions", "future_trends", "confidence_intervals"]
        present_predictive = [field for field in predictive_fields if field in historical_data]
        print(f"IP {ip_address} predictive fields: {', '.join(present_predictive)}")
        
        # Check for data quality and coverage metrics
        quality_fields = ["data_coverage", "quality_score", "completeness", "reliability_metrics"]
        present_quality = [field for field in quality_fields if field in historical_data]
        print(f"IP {ip_address} quality fields: {', '.join(present_quality)}")
        
        # Validate data coverage if present
        if "data_coverage" in historical_data:
            coverage = historical_data["data_coverage"]
            assert isinstance(coverage, dict), "Data coverage should be a dictionary"
            
            coverage_metrics = ["temporal_coverage", "data_completeness", "source_reliability"]
            present_coverage = [field for field in coverage_metrics if field in coverage]
            print(f"Data coverage contains: {', '.join(present_coverage)}")
        
        # Check for comparative analysis and benchmarking
        comparative_fields = ["baseline_comparison", "peer_analysis", "market_benchmarks", "relative_performance"]
        present_comparative = [field for field in comparative_fields if field in historical_data]
        print(f"IP {ip_address} comparative fields: {', '.join(present_comparative)}")
        
        # Check for intelligence feed historical context
        if intelligence_feeds:
            feed_history_fields = ["feed_evolution", "source_changes", "data_provenance", "feed_reliability_history"]
            present_feed_history = [field for field in feed_history_fields if field in historical_data]
            if present_feed_history:
                print(f"IP {ip_address} feed history fields: {', '.join(present_feed_history)}")
        
        # Log the structure of the first result for debugging
        if scenario == test_scenarios[0]:
            print(f"Example historical analysis structure: {list(historical_data.keys())}")

        # Brief delay between requests to respect rate limiting
        import asyncio
        await asyncio.sleep(0.2)

    print(f"Successfully retrieved and validated Digital Envoy historical analysis data for {len(test_scenarios)} IP scenarios")

    return True