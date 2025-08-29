# 4-test_get_indicators.py

async def test_get_indicators(zerg_state=None):
    """Test Recorded Future threat intelligence indicators retrieval"""
    print("Testing Recorded Future threat indicators retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    rf_api_url = zerg_state.get("recorded_future_api_url").get("value")
    rf_api_token = zerg_state.get("recorded_future_api_token").get("value")

    from connectors.recorded_future.config import RecordedFutureConnectorConfig
    from connectors.recorded_future.connector import RecordedFutureConnector
    from connectors.recorded_future.target import RecordedFutureTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = RecordedFutureConnectorConfig(
        api_url=rf_api_url,
        api_token=rf_api_token
    )
    assert isinstance(config, ConnectorConfig), "RecordedFutureConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = RecordedFutureConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RecordedFutureConnector should be of type Connector"

    # get query target options
    rf_query_target_options = await connector.get_query_target_options()
    assert isinstance(rf_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select indicators intelligence source
    intelligence_source_selector = None
    for selector in rf_query_target_options.selectors:
        if selector.type == 'intelligence_sources':  
            intelligence_source_selector = selector
            break

    assert intelligence_source_selector, "failed to retrieve intelligence source selector from query target options"
    assert isinstance(intelligence_source_selector.values, list), "intelligence_source_selector values must be a list"
    
    # Find indicators in available intelligence sources
    indicators_source = None
    for source in intelligence_source_selector.values:
        if 'indicator' in source.lower() or 'ioc' in source.lower():
            indicators_source = source
            break
    
    assert indicators_source, "Indicators intelligence source not found in available options"
    print(f"Selecting indicators intelligence source: {indicators_source}")

    # set up the target with indicators intelligence source
    target = RecordedFutureTarget(intelligence_sources=[indicators_source])
    assert isinstance(target, ConnectorTargetInterface), "RecordedFutureTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_recorded_future_indicators tool
    rf_get_indicators_tool = next(tool for tool in tools if tool.name == "get_recorded_future_indicators")
    indicators_result = await rf_get_indicators_tool.execute()
    indicators_data = indicators_result.result

    print("Type of returned indicators data:", type(indicators_data))
    print(f"Indicators count: {len(indicators_data)} sample: {str(indicators_data)[:200]}")

    # Verify that indicators_data is a list
    assert isinstance(indicators_data, list), "Indicators data should be a list"
    assert len(indicators_data) > 0, "Indicators data should not be empty"
    
    # Limit the number of indicators to check if there are many
    indicators_to_check = indicators_data[:5] if len(indicators_data) > 5 else indicators_data
    
    # Verify structure of each indicator entry
    for indicator in indicators_to_check:
        # Verify essential indicator fields based on Recorded Future API structure
        assert "entity" in indicator, "Each indicator should have an 'entity' field"
        assert "type" in indicator, "Each indicator should have a 'type' field"
        assert "risk" in indicator, "Each indicator should have a 'risk' field"
        
        # Verify entity structure
        entity = indicator["entity"]
        assert "id" in entity, "Entity should have an 'id' field"
        assert "name" in entity, "Entity should have a 'name' field"
        assert "type" in entity, "Entity should have a 'type' field"
        
        # Verify risk structure
        risk = indicator["risk"]
        assert "score" in risk, "Risk should have a 'score' field"
        assert isinstance(risk["score"], (int, float)), "Risk score should be numeric"
        assert 0 <= risk["score"] <= 100, "Risk score should be between 0 and 100"
        
        # Verify indicator type is valid
        valid_types = ["ip", "domain", "hash", "url", "malware", "vulnerability"]
        entity_type = entity["type"].lower()
        assert any(vtype in entity_type for vtype in valid_types), f"Invalid entity type: {entity_type}"
        
        # Check for additional fields
        optional_fields = ["evidence", "timestamps", "context"]
        present_fields = [field for field in optional_fields if field in indicator]
        
        print(f"Indicator {entity['name']} (type: {entity['type']}, risk: {risk['score']}) contains: {', '.join(present_fields)}")
        
        # Log the structure of the first indicator for debugging
        if indicator == indicators_to_check[0]:
            print(f"Example indicator structure: {indicator}")

    print(f"Successfully retrieved and validated {len(indicators_data)} Recorded Future threat indicators")

    return True