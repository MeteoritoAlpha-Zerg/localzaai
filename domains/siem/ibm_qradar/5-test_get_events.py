# 5-test_get_events.py

async def test_get_events(zerg_state=None):
    """Test IBM QRadar security events retrieval"""
    print("Testing IBM QRadar security events retrieval")

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

    # select events data source
    data_source_selector = None
    for selector in ibm_qradar_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find events in available data sources
    events_source = None
    for source in data_source_selector.values:
        if 'event' in source.lower():
            events_source = source
            break
    
    assert events_source, "Events data source not found in available options"
    print(f"Selecting events data source: {events_source}")

    # set up the target with events data source
    target = IBMQRadarTarget(data_sources=[events_source])
    assert isinstance(target, ConnectorTargetInterface), "IBMQRadarTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_ibm_qradar_events tool and execute it
    get_ibm_qradar_events_tool = next(tool for tool in tools if tool.name == "get_ibm_qradar_events")
    events_result = await get_ibm_qradar_events_tool.execute()
    events_data = events_result.result

    print("Type of returned events data:", type(events_data))
    print(f"Events count: {len(events_data)} sample: {str(events_data)[:200]}")

    # Verify that events_data is a list
    assert isinstance(events_data, list), "Events data should be a list"
    assert len(events_data) > 0, "Events data should not be empty"
    
    # Limit the number of events to check if there are many
    events_to_check = events_data[:10] if len(events_data) > 10 else events_data
    
    # Verify structure of each event entry
    for event in events_to_check:
        # Verify essential event fields per IBM QRadar API specification
        assert "qid" in event, "Each event should have a 'qid' field"
        assert "starttime" in event, "Each event should have a 'starttime' field"
        assert "categoryname" in event, "Each event should have a 'categoryname' field"
        assert "logsourcename" in event, "Each event should have a 'logsourcename' field"
        
        # Verify QID is not empty
        assert event["qid"], "QID should not be empty"
        
        # Verify start time is not empty
        assert event["starttime"], "Start time should not be empty"
        
        # Verify category name is not empty
        assert event["categoryname"].strip(), "Category name should not be empty"
        
        # Verify log source name is not empty
        assert event["logsourcename"].strip(), "Log source name should not be empty"
        
        # Check for additional event fields per IBM QRadar specification
        event_fields = ["eventdirection", "eventcount", "magnitude", "severity", "credibility", "relevance", "sourceip", "destinationip", "username", "protocolname"]
        present_fields = [field for field in event_fields if field in event]
        
        print(f"Event (QID: {event['qid']}, category: {event['categoryname']}) contains: {', '.join(present_fields)}")
        
        # If magnitude is present, validate it's within valid range
        if "magnitude" in event:
            magnitude = event["magnitude"]
            assert isinstance(magnitude, (int, float)), "Magnitude should be numeric"
            assert 1 <= magnitude <= 10, f"Magnitude should be between 1 and 10: {magnitude}"
        
        # If severity is present, validate it's within valid range
        if "severity" in event:
            severity = event["severity"]
            assert isinstance(severity, (int, float)), "Severity should be numeric"
            assert 1 <= severity <= 10, f"Severity should be between 1 and 10: {severity}"
        
        # If credibility is present, validate it's within valid range
        if "credibility" in event:
            credibility = event["credibility"]
            assert isinstance(credibility, (int, float)), "Credibility should be numeric"
            assert 1 <= credibility <= 10, f"Credibility should be between 1 and 10: {credibility}"
        
        # If relevance is present, validate it's within valid range
        if "relevance" in event:
            relevance = event["relevance"]
            assert isinstance(relevance, (int, float)), "Relevance should be numeric"
            assert 1 <= relevance <= 10, f"Relevance should be between 1 and 10: {relevance}"
        
        # If event count is present, verify it's numeric
        if "eventcount" in event:
            event_count = event["eventcount"]
            assert isinstance(event_count, int), "Event count should be an integer"
            assert event_count >= 0, "Event count should be non-negative"
        
        # If source IP is present, validate basic format
        if "sourceip" in event:
            source_ip = event["sourceip"]
            assert source_ip and source_ip.strip(), "Source IP should not be empty"
        
        # If destination IP is present, validate basic format
        if "destinationip" in event:
            dest_ip = event["destinationip"]
            assert dest_ip and dest_ip.strip(), "Destination IP should not be empty"
        
        # If username is present, validate it's not empty
        if "username" in event:
            username = event["username"]
            assert username and username.strip(), "Username should not be empty"
        
        # If protocol name is present, validate it's not empty
        if "protocolname" in event:
            protocol_name = event["protocolname"]
            assert protocol_name and protocol_name.strip(), "Protocol name should not be empty"
        
        # Log the structure of the first event for debugging
        if event == events_to_check[0]:
            print(f"Example event structure: {event}")

    print(f"Successfully retrieved and validated {len(events_data)} IBM QRadar events")

    return True