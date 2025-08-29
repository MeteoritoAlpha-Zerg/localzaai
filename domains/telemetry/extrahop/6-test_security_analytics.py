# 6-test_security_analytics.py

async def test_security_analytics(zerg_state=None):
    """Test ExtraHop network security analytics generation"""
    print("Attempting to generate security analytics using ExtraHop connector")

    assert zerg_state, "this test requires valid zerg_state"

    extrahop_server_url = zerg_state.get("extrahop_server_url").get("value")
    extrahop_api_key = zerg_state.get("extrahop_api_key").get("value")
    extrahop_api_secret = zerg_state.get("extrahop_api_secret").get("value")

    from connectors.extrahop.config import ExtraHopConnectorConfig
    from connectors.extrahop.connector import ExtraHopConnector
    from connectors.extrahop.tools import ExtraHopConnectorTools, GenerateSecurityAnalyticsInput
    from connectors.extrahop.target import ExtraHopTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ExtraHopConnectorConfig(
        server_url=extrahop_server_url,
        api_key=extrahop_api_key,
        api_secret=extrahop_api_secret
    )
    assert isinstance(config, ConnectorConfig), "ExtraHopConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ExtraHopConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ExtraHopConnector should be of type Connector"

    # get query target options for sensor networks
    extrahop_query_target_options = await connector.get_query_target_options()
    assert isinstance(extrahop_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select sensor networks to target
    sensor_network_selector = None
    for selector in extrahop_query_target_options.selectors:
        if selector.type == 'sensor_network_ids':  
            sensor_network_selector = selector
            break

    assert sensor_network_selector, "failed to retrieve sensor network selector from query target options"

    assert isinstance(sensor_network_selector.values, list), "sensor_network_selector values must be a list"
    sensor_network_id = sensor_network_selector.values[0] if sensor_network_selector.values else None
    print(f"Selecting sensor network ID: {sensor_network_id}")

    assert sensor_network_id, f"failed to retrieve sensor network ID from sensor network selector"

    # set up the target with sensor network ID
    target = ExtraHopTarget(sensor_network_ids=[sensor_network_id])
    assert isinstance(target, ConnectorTargetInterface), "ExtraHopTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the generate_security_analytics tool
    generate_security_analytics_tool = next(tool for tool in tools if tool.name == "generate_security_analytics")
    
    # Test security analytics generation
    security_analytics_result = await generate_security_analytics_tool.execute(
        sensor_network_id=sensor_network_id,
        time_period="1h",
        include_behavioral_analysis=True
    )
    security_analytics = security_analytics_result.result

    print("Type of returned security analytics:", type(security_analytics))
    print(f"Security analytics data: {str(security_analytics)[:300]}")

    # Verify that security_analytics is a dictionary with expected structure
    assert isinstance(security_analytics, dict), "security_analytics should be a dictionary"
    
    # Verify essential security analytics fields
    assert "network_summary" in security_analytics, "Security analytics should have a 'network_summary' field"
    assert "threat_analysis" in security_analytics, "Security analytics should have a 'threat_analysis' field"
    assert "device_analysis" in security_analytics, "Security analytics should have a 'device_analysis' field"
    
    # Verify network summary structure
    network_summary = security_analytics["network_summary"]
    assert isinstance(network_summary, dict), "network_summary should be a dictionary"
    
    summary_fields = ["total_devices", "total_traffic", "active_protocols"]
    present_summary_fields = [field for field in summary_fields if field in network_summary]
    
    print(f"Network summary contains: {', '.join(present_summary_fields)}")
    
    # Verify threat analysis if present
    threat_analysis = security_analytics["threat_analysis"]
    assert isinstance(threat_analysis, dict), "threat_analysis should be a dictionary"
    
    threat_fields = ["anomaly_count", "risk_distribution", "top_threats"]
    present_threat_fields = [field for field in threat_fields if field in threat_analysis]
    
    print(f"Threat analysis contains: {', '.join(present_threat_fields)}")
    
    # Test real-time monitoring if available
    if "get_realtime_monitoring" in [tool.name for tool in tools]:
        get_realtime_tool = next(tool for tool in tools if tool.name == "get_realtime_monitoring")
        realtime_result = await get_realtime_tool.execute(
            sensor_network_id=sensor_network_id
        )
        realtime_data = realtime_result.result
        
        if realtime_data:
            assert isinstance(realtime_data, dict), "Realtime data should be a dictionary"
            
            realtime_fields = ["current_alerts", "live_metrics", "active_sessions"]
            present_realtime_fields = [field for field in realtime_fields if field in realtime_data]
            
            print(f"Real-time monitoring contains: {', '.join(present_realtime_fields)}")
    
    # Test device behavior analysis if available
    if "get_device_behavior" in [tool.name for tool in tools]:
        get_device_behavior_tool = next(tool for tool in tools if tool.name == "get_device_behavior")
        device_behavior_result = await get_device_behavior_tool.execute(
            sensor_network_id=sensor_network_id,
            analysis_type="behavioral_baseline"
        )
        device_behavior = device_behavior_result.result
        
        if device_behavior:
            assert isinstance(device_behavior, list), "Device behavior should be a list"
            
            if len(device_behavior) > 0:
                first_device = device_behavior[0]
                assert "device_id" in first_device, "Each device should have device_id"
                
                print(f"Device behavior analysis contains {len(device_behavior)} devices")

    print(f"Successfully generated network security analytics")

    return True