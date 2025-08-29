# 6-test_network_telemetry.py

async def test_network_telemetry(zerg_state=None):
    """Test Netography network telemetry and real-time monitoring"""
    print("Testing Netography network telemetry and real-time monitoring")

    assert zerg_state, "this test requires valid zerg_state"

    netography_api_token = zerg_state.get("netography_api_token").get("value")
    netography_base_url = zerg_state.get("netography_base_url").get("value")
    netography_tenant_id = zerg_state.get("netography_tenant_id").get("value")

    from connectors.netography.config import NetographyConnectorConfig
    from connectors.netography.connector import NetographyConnector
    from connectors.netography.target import NetographyTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = NetographyConnectorConfig(
        api_token=netography_api_token,
        base_url=netography_base_url,
        tenant_id=netography_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "NetographyConnectorConfig should be of type ConnectorConfig"

    connector = NetographyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "NetographyConnector should be of type Connector"

    netography_query_target_options = await connector.get_query_target_options()
    assert isinstance(netography_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    sensor_selector = None
    for selector in netography_query_target_options.selectors:
        if selector.type == 'sensor_ids':  
            sensor_selector = selector
            break

    assert sensor_selector, "failed to retrieve sensor selector from query target options"

    assert isinstance(sensor_selector.values, list), "sensor_selector values must be a list"
    sensor_id = sensor_selector.values[0] if sensor_selector.values else None
    print(f"Using sensor for network telemetry analysis: {sensor_id}")

    assert sensor_id, f"failed to retrieve sensor ID from sensor selector"

    target = NetographyTarget(sensor_ids=[sensor_id])
    assert isinstance(target, ConnectorTargetInterface), "NetographyTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_network_telemetry_tool = next(tool for tool in tools if tool.name == "get_network_telemetry")
    
    telemetry_result = await get_network_telemetry_tool.execute(
        sensor_id=sensor_id,
        time_window_hours=24
    )
    network_telemetry = telemetry_result.result

    print("Type of returned network_telemetry:", type(network_telemetry))
    print(f"Network telemetry preview: {str(network_telemetry)[:200]}")

    assert network_telemetry is not None, "network_telemetry should not be None"
    
    if isinstance(network_telemetry, dict):
        expected_fields = ["sensor_id", "metrics", "flows", "anomalies", "behavioral_analytics"]
        present_fields = [field for field in expected_fields if field in network_telemetry]
        
        if len(present_fields) > 0:
            print(f"Network telemetry contains these fields: {', '.join(present_fields)}")
            
            if "metrics" in network_telemetry:
                metrics = network_telemetry["metrics"]
                assert isinstance(metrics, dict), "Metrics should be a dictionary"
                
                metric_fields = ["bandwidth", "packet_count", "connection_count", "anomaly_score"]
                present_metrics = [field for field in metric_fields if field in metrics]
                print(f"Metrics contain: {', '.join(present_metrics)}")
            
            if "flows" in network_telemetry:
                flows = network_telemetry["flows"]
                assert isinstance(flows, list), "Flows should be a list"
                print(f"Found {len(flows)} network flows")
            
            if "anomalies" in network_telemetry:
                anomalies = network_telemetry["anomalies"]
                assert isinstance(anomalies, list), "Anomalies should be a list"
                print(f"Found {len(anomalies)} anomalies")
        
        print(f"Network telemetry structure: {network_telemetry}")
        
    elif isinstance(network_telemetry, list):
        assert len(network_telemetry) > 0, "Network telemetry list should not be empty"
        
        sample_item = network_telemetry[0]
        assert isinstance(sample_item, dict), "Telemetry items should be dictionaries"
        
        item_fields = ["timestamp", "source", "destination", "protocol", "bytes", "packets"]
        present_item_fields = [field for field in item_fields if field in sample_item]
        
        print(f"Telemetry items contain these fields: {', '.join(present_item_fields)}")
        print(f"Example telemetry item: {sample_item}")
        
    else:
        assert str(network_telemetry).strip() != "", "Network telemetry should contain meaningful data"

    print(f"Successfully retrieved and validated network telemetry data")

    return True