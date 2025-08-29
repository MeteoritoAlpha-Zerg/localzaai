# 5-test_security_alerts.py

async def test_security_alerts(zerg_state=None):
    """Test Netography security alert retrieval"""
    print("Testing Netography security alert retrieval")

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
    print(f"Selecting sensor ID: {sensor_id}")

    assert sensor_id, f"failed to retrieve sensor ID from sensor selector"

    target = NetographyTarget(sensor_ids=[sensor_id])
    assert isinstance(target, ConnectorTargetInterface), "NetographyTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_security_alerts_tool = next(tool for tool in tools if tool.name == "get_security_alerts")
    security_alerts_result = await get_security_alerts_tool.execute(sensor_id=sensor_id)
    security_alerts = security_alerts_result.result

    print("Type of returned security_alerts:", type(security_alerts))
    print(f"len alerts: {len(security_alerts)} alerts: {str(security_alerts)[:200]}")

    assert isinstance(security_alerts, list), "security_alerts should be a list"
    assert len(security_alerts) > 0, "security_alerts should not be empty"
    
    alerts_to_check = security_alerts[:3] if len(security_alerts) > 3 else security_alerts
    
    for alert in alerts_to_check:
        assert isinstance(alert, dict), "Each alert should be a dictionary"
        assert "id" in alert, "Each alert should have an 'id' field"
        assert "severity" in alert, "Each alert should have a 'severity' field"
        assert "timestamp" in alert, "Each alert should have a 'timestamp' field"
        
        if "severity" in alert:
            valid_severities = ["low", "medium", "high", "critical"]
            assert alert["severity"] in valid_severities, f"Alert severity should be valid"
        
        alert_fields = ["title", "description", "source_ip", "dest_ip", "anomaly_type", "confidence"]
        present_fields = [field for field in alert_fields if field in alert]
        
        print(f"Alert {alert['id']} contains these fields: {', '.join(present_fields)}")
        
        if "confidence" in alert:
            confidence = alert["confidence"]
            assert isinstance(confidence, (int, float)), "Confidence should be numeric"
            assert 0 <= confidence <= 100, "Confidence should be between 0 and 100"
        
        if alert == alerts_to_check[0]:
            print(f"Example alert structure: {alert}")

    print(f"Successfully retrieved and validated {len(security_alerts)} security alerts")

    return True