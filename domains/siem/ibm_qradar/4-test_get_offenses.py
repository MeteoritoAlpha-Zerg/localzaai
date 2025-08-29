# 4-test_get_offenses.py

async def test_get_offenses(zerg_state=None):
    """Test IBM QRadar security offenses retrieval"""
    print("Testing IBM QRadar security offenses retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    ibm_qradar_api_url = zerg_state.get("ibm_qradar_api_url").get("value")
    ibm_qradar_api_token = zerg_state.get("ibm_qradar_api_token").get("value")

    from connectors.ibm_qradar.config import IBMQRadarConnectorConfig
    from connectors.ibm_qradar.connector import IBMQRadarConnector
    from connectors.ibm_qradar.target import IBMQRadarTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = IBMQRadarConnectorConfig(
        api_url=ibm_qradar_api_url,
        api_token=ibm_qradar_api_token
    )
    assert isinstance(config, ConnectorConfig), "IBMQRadarConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = IBMQRadarConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "IBMQRadarConnector should be of type Connector"

    # get query target options
    ibm_qradar_query_target_options = await connector.get_query_target_options()
    assert isinstance(ibm_qradar_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select offenses data source
    data_source_selector = None
    for selector in ibm_qradar_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find offenses in available data sources
    offenses_source = None
    for source in data_source_selector.values:
        if 'offense' in source.lower():
            offenses_source = source
            break
    
    assert offenses_source, "Offenses data source not found in available options"
    print(f"Selecting offenses data source: {offenses_source}")

    # set up the target with offenses data source
    target = IBMQRadarTarget(data_sources=[offenses_source])
    assert isinstance(target, ConnectorTargetInterface), "IBMQRadarTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_ibm_qradar_offenses tool
    ibm_qradar_get_offenses_tool = next(tool for tool in tools if tool.name == "get_ibm_qradar_offenses")
    offenses_result = await ibm_qradar_get_offenses_tool.execute()
    offenses_data = offenses_result.result

    print("Type of returned offenses data:", type(offenses_data))
    print(f"Offenses count: {len(offenses_data)} sample: {str(offenses_data)[:200]}")

    # Verify that offenses_data is a list
    assert isinstance(offenses_data, list), "Offenses data should be a list"
    assert len(offenses_data) > 0, "Offenses data should not be empty"
    
    # Limit the number of offenses to check if there are many
    offenses_to_check = offenses_data[:5] if len(offenses_data) > 5 else offenses_data
    
    # Verify structure of each offense entry
    for offense in offenses_to_check:
        # Verify essential offense fields per IBM QRadar API specification
        assert "id" in offense, "Each offense should have an 'id' field"
        assert "magnitude" in offense, "Each offense should have a 'magnitude' field"
        assert "status" in offense, "Each offense should have a 'status' field"
        assert "start_time" in offense, "Each offense should have a 'start_time' field"
        
        # Verify offense status is valid
        valid_statuses = ["OPEN", "HIDDEN", "CLOSED"]
        status = offense["status"]
        assert status in valid_statuses, f"Invalid offense status: {status}"
        
        # Verify magnitude is numeric and within valid range
        magnitude = offense["magnitude"]
        assert isinstance(magnitude, (int, float)), "Magnitude should be numeric"
        assert 1 <= magnitude <= 10, f"Magnitude should be between 1 and 10: {magnitude}"
        
        # Verify offense ID is not empty
        assert offense["id"], "Offense ID should not be empty"
        
        # Check for additional offense fields per IBM QRadar specification
        offense_fields = ["description", "offense_type", "severity", "credibility", "relevance", "event_count", "flow_count", "assigned_to", "categories"]
        present_fields = [field for field in offense_fields if field in offense]
        
        print(f"Offense {offense['id']} (magnitude: {offense['magnitude']}, status: {offense['status']}) contains: {', '.join(present_fields)}")
        
        # If severity is present, validate it's within valid range
        if "severity" in offense:
            severity = offense["severity"]
            assert isinstance(severity, (int, float)), "Severity should be numeric"
            assert 1 <= severity <= 10, f"Severity should be between 1 and 10: {severity}"
        
        # If credibility is present, validate it's within valid range
        if "credibility" in offense:
            credibility = offense["credibility"]
            assert isinstance(credibility, (int, float)), "Credibility should be numeric"
            assert 1 <= credibility <= 10, f"Credibility should be between 1 and 10: {credibility}"
        
        # If relevance is present, validate it's within valid range
        if "relevance" in offense:
            relevance = offense["relevance"]
            assert isinstance(relevance, (int, float)), "Relevance should be numeric"
            assert 1 <= relevance <= 10, f"Relevance should be between 1 and 10: {relevance}"
        
        # If event count is present, verify it's numeric
        if "event_count" in offense:
            event_count = offense["event_count"]
            assert isinstance(event_count, int), "Event count should be an integer"
            assert event_count >= 0, "Event count should be non-negative"
        
        # If flow count is present, verify it's numeric
        if "flow_count" in offense:
            flow_count = offense["flow_count"]
            assert isinstance(flow_count, int), "Flow count should be an integer"
            assert flow_count >= 0, "Flow count should be non-negative"
        
        # If description is present, validate it's not empty
        if "description" in offense:
            description = offense["description"]
            assert description and description.strip(), "Description should not be empty"
        
        # If categories are present, validate structure
        if "categories" in offense:
            categories = offense["categories"]
            assert isinstance(categories, list), "Categories should be a list"
            for category in categories:
                assert isinstance(category, str), "Each category should be a string"
                assert category.strip(), "Category should not be empty"
        
        # Log the structure of the first offense for debugging
        if offense == offenses_to_check[0]:
            print(f"Example offense structure: {offense}")

    print(f"Successfully retrieved and validated {len(offenses_data)} IBM QRadar offenses")

    return True