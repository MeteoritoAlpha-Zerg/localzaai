# 4-test_get_investigations.py

async def test_get_investigations(zerg_state=None):
    """Test Rapid7 InsightIDR security investigations retrieval"""
    print("Testing Rapid7 InsightIDR security investigations retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    rapid7_insightidr_api_url = zerg_state.get("rapid7_insightidr_api_url").get("value")
    rapid7_insightidr_api_key = zerg_state.get("rapid7_insightidr_api_key").get("value")

    from connectors.rapid7_insightidr.config import Rapid7InsightIDRConnectorConfig
    from connectors.rapid7_insightidr.connector import Rapid7InsightIDRConnector
    from connectors.rapid7_insightidr.target import Rapid7InsightIDRTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = Rapid7InsightIDRConnectorConfig(
        api_url=rapid7_insightidr_api_url,
        api_key=rapid7_insightidr_api_key
    )
    assert isinstance(config, ConnectorConfig), "Rapid7InsightIDRConnectorConfig should be of type ConnectorConfig"

    connector = Rapid7InsightIDRConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "Rapid7InsightIDRConnector should be of type Connector"

    rapid7_insightidr_query_target_options = await connector.get_query_target_options()
    assert isinstance(rapid7_insightidr_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in rapid7_insightidr_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    investigations_source = None
    for source in data_source_selector.values:
        if 'investigation' in source.lower():
            investigations_source = source
            break
    
    assert investigations_source, "Investigations data source not found in available options"
    print(f"Selecting investigations data source: {investigations_source}")

    target = Rapid7InsightIDRTarget(data_sources=[investigations_source])
    assert isinstance(target, ConnectorTargetInterface), "Rapid7InsightIDRTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    rapid7_insightidr_get_investigations_tool = next(tool for tool in tools if tool.name == "get_rapid7_insightidr_investigations")
    investigations_result = await rapid7_insightidr_get_investigations_tool.execute()
    investigations_data = investigations_result.result

    print("Type of returned investigations data:", type(investigations_data))
    print(f"Investigations count: {len(investigations_data)} sample: {str(investigations_data)[:200]}")

    assert isinstance(investigations_data, list), "Investigations data should be a list"
    assert len(investigations_data) > 0, "Investigations data should not be empty"
    
    investigations_to_check = investigations_data[:5] if len(investigations_data) > 5 else investigations_data
    
    for investigation in investigations_to_check:
        # Verify essential investigation fields
        assert "rrn" in investigation, "Each investigation should have an 'rrn' field"
        assert "title" in investigation, "Each investigation should have a 'title' field"
        assert "status" in investigation, "Each investigation should have a 'status' field"
        assert "priority" in investigation, "Each investigation should have a 'priority' field"
        assert "created_time" in investigation, "Each investigation should have a 'created_time' field"
        
        # Verify investigation status is valid
        valid_statuses = ["OPEN", "CLOSED", "INVESTIGATING"]
        status = investigation["status"]
        assert status in valid_statuses, f"Invalid investigation status: {status}"
        
        # Verify priority is valid
        valid_priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        priority = investigation["priority"]
        assert priority in valid_priorities, f"Invalid priority level: {priority}"
        
        investigation_fields = ["assignee", "source", "disposition", "alerts", "first_alert_time", "last_alert_time"]
        present_fields = [field for field in investigation_fields if field in investigation]
        
        print(f"Investigation {investigation['rrn']} ({investigation['priority']}, {investigation['status']}) contains: {', '.join(present_fields)}")
        
        assert investigation["rrn"], "Investigation RRN should not be empty"
        assert investigation["title"].strip(), "Investigation title should not be empty"
        
        # Log the structure of the first investigation for debugging
        if investigation == investigations_to_check[0]:
            print(f"Example investigation structure: {investigation}")

    print(f"Successfully retrieved and validated {len(investigations_data)} Rapid7 InsightIDR investigations")

    return True