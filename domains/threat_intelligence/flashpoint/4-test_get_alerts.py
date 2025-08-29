# 4-test_get_alerts.py

async def test_get_alerts(zerg_state=None):
    """Test Flashpoint threat intelligence alerts retrieval"""
    print("Testing Flashpoint threat intelligence alerts retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    flashpoint_api_url = zerg_state.get("flashpoint_api_url").get("value")
    flashpoint_api_key = zerg_state.get("flashpoint_api_key").get("value")

    from connectors.flashpoint.config import FlashpointConnectorConfig
    from connectors.flashpoint.connector import FlashpointConnector
    from connectors.flashpoint.target import FlashpointTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = FlashpointConnectorConfig(
        api_url=flashpoint_api_url,
        api_key=flashpoint_api_key
    )
    assert isinstance(config, ConnectorConfig), "FlashpointConnectorConfig should be of type ConnectorConfig"

    connector = FlashpointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "FlashpointConnector should be of type Connector"

    flashpoint_query_target_options = await connector.get_query_target_options()
    assert isinstance(flashpoint_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in flashpoint_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    alerts_source = None
    for source in data_source_selector.values:
        if 'alert' in source.lower():
            alerts_source = source
            break
    
    assert alerts_source, "Alerts data source not found in available options"
    print(f"Selecting alerts data source: {alerts_source}")

    target = FlashpointTarget(data_sources=[alerts_source])
    assert isinstance(target, ConnectorTargetInterface), "FlashpointTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    flashpoint_get_alerts_tool = next(tool for tool in tools if tool.name == "get_flashpoint_alerts")
    alerts_result = await flashpoint_get_alerts_tool.execute()
    alerts_data = alerts_result.result

    print("Type of returned alerts data:", type(alerts_data))
    print(f"Alerts count: {len(alerts_data)} sample: {str(alerts_data)[:200]}")

    assert isinstance(alerts_data, list), "Alerts data should be a list"
    assert len(alerts_data) > 0, "Alerts data should not be empty"
    
    alerts_to_check = alerts_data[:5] if len(alerts_data) > 5 else alerts_data
    
    for alert in alerts_to_check:
        # Verify essential alert fields per Flashpoint API specification
        assert "uuid" in alert, "Each alert should have a 'uuid' field"
        assert "title" in alert, "Each alert should have a 'title' field"
        assert "summary" in alert, "Each alert should have a 'summary' field"
        assert "created_at" in alert, "Each alert should have a 'created_at' field"
        
        assert alert["uuid"], "Alert UUID should not be empty"
        assert alert["title"].strip(), "Alert title should not be empty"
        assert alert["created_at"], "Created at should not be empty"
        
        alert_fields = ["tags", "sources", "threat_type", "confidence", "severity", "indicators"]
        present_fields = [field for field in alert_fields if field in alert]
        
        print(f"Alert {alert['uuid'][:8]}... ({alert['title'][:50]}) contains: {', '.join(present_fields)}")
        
        # If confidence is present, validate it's numeric
        if "confidence" in alert:
            confidence = alert["confidence"]
            assert isinstance(confidence, (int, float)), "Confidence should be numeric"
            assert 0 <= confidence <= 100, f"Confidence should be between 0 and 100: {confidence}"
        
        # If severity is present, validate it's valid
        if "severity" in alert:
            severity = alert["severity"].lower()
            valid_severities = ["low", "medium", "high", "critical"]
            assert severity in valid_severities, f"Invalid severity level: {severity}"
        
        # If tags are present, validate structure
        if "tags" in alert:
            tags = alert["tags"]
            assert isinstance(tags, list), "Tags should be a list"
            for tag in tags:
                assert isinstance(tag, str), "Each tag should be a string"
                assert tag.strip(), "Tag should not be empty"
        
        # If indicators are present, validate structure
        if "indicators" in alert:
            indicators = alert["indicators"]
            assert isinstance(indicators, list), "Indicators should be a list"
            for indicator in indicators:
                assert isinstance(indicator, dict), "Each indicator should be a dictionary"
                assert "value" in indicator, "Each indicator should have a value"
                assert indicator["value"].strip(), "Indicator value should not be empty"
        
        # Log the structure of the first alert for debugging
        if alert == alerts_to_check[0]:
            print(f"Example alert structure: {alert}")

    print(f"Successfully retrieved and validated {len(alerts_data)} Flashpoint alerts")

    return True