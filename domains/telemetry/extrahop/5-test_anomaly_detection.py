# 5-test_anomaly_detection.py

async def test_anomaly_detection(zerg_state=None):
    """Test ExtraHop anomaly detection data retrieval"""
    print("Attempting to retrieve anomaly detection data using ExtraHop connector")

    assert zerg_state, "this test requires valid zerg_state"

    extrahop_server_url = zerg_state.get("extrahop_server_url").get("value")
    extrahop_api_key = zerg_state.get("extrahop_api_key").get("value")
    extrahop_api_secret = zerg_state.get("extrahop_api_secret").get("value")

    from connectors.extrahop.config import ExtraHopConnectorConfig
    from connectors.extrahop.connector import ExtraHopConnector
    from connectors.extrahop.tools import ExtraHopConnectorTools, GetAnomalyDataInput
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

    # get query target options
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

    # grab the get_anomaly_detection tool and execute it
    get_anomaly_detection_tool = next(tool for tool in tools if tool.name == "get_anomaly_detection")
    anomaly_detection_result = await get_anomaly_detection_tool.execute(sensor_network_id=sensor_network_id)
    anomaly_detection = anomaly_detection_result.result

    print("Type of returned anomaly_detection:", type(anomaly_detection))
    print(f"Anomaly detection data: {str(anomaly_detection)[:200]}")

    # Verify that anomaly_detection is a list
    assert isinstance(anomaly_detection, list), "anomaly_detection should be a list"
    assert len(anomaly_detection) > 0, "anomaly_detection should not be empty"
    
    # Limit the number of anomalies to check if there are many
    anomalies_to_check = anomaly_detection[:5] if len(anomaly_detection) > 5 else anomaly_detection
    
    # Verify structure of each anomaly object
    for anomaly in anomalies_to_check:
        # Verify essential ExtraHop anomaly fields
        assert "detection_id" in anomaly, "Each anomaly should have a 'detection_id' field"
        assert "timestamp" in anomaly, "Each anomaly should have a 'timestamp' field"
        assert "risk_score" in anomaly, "Each anomaly should have a 'risk_score' field"
        assert "category" in anomaly, "Each anomaly should have a 'category' field"
        
        # Verify common ExtraHop anomaly fields
        assert "type" in anomaly, "Each anomaly should have a 'type' field"
        assert "description" in anomaly, "Each anomaly should have a 'description' field"
        
        # Check for additional optional fields
        optional_fields = ["devices", "protocols", "threat_indicators", "mitigation_status"]
        present_optional = [field for field in optional_fields if field in anomaly]
        
        print(f"Anomaly {anomaly['detection_id']} (risk: {anomaly['risk_score']}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first anomaly for debugging
        if anomaly == anomalies_to_check[0]:
            print(f"Example anomaly structure: {anomaly}")

    # Test threat indicator extraction if available
    if "get_threat_indicators" in [tool.name for tool in tools]:
        get_threat_indicators_tool = next(tool for tool in tools if tool.name == "get_threat_indicators")
        threat_indicators_result = await get_threat_indicators_tool.execute(
            sensor_network_id=sensor_network_id,
            time_range="1h"
        )
        threat_indicators = threat_indicators_result.result
        
        if threat_indicators:
            assert isinstance(threat_indicators, list), "Threat indicators should be a list"
            print(f"Retrieved {len(threat_indicators)} threat indicators")

    print(f"Successfully retrieved and validated {len(anomaly_detection)} ExtraHop anomaly detections")

    return True