# 6-test_udm_search.py

async def test_udm_search(zerg_state=None):
    """Test Google Chronicle UDM search and analytics functionality"""
    print("Attempting to execute UDM searches using Google Chronicle connector")

    assert zerg_state, "this test requires valid zerg_state"

    chronicle_service_account_path = zerg_state.get("chronicle_service_account_path").get("value")
    chronicle_customer_id = zerg_state.get("chronicle_customer_id").get("value")

    from connectors.chronicle.config import ChronicleConnectorConfig
    from connectors.chronicle.connector import ChronicleConnector
    from connectors.chronicle.tools import ChronicleConnectorTools, ExecuteUDMSearchInput
    from connectors.chronicle.target import ChronicleTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ChronicleConnectorConfig(
        service_account_path=chronicle_service_account_path,
        customer_id=chronicle_customer_id
    )
    assert isinstance(config, ConnectorConfig), "ChronicleConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ChronicleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ChronicleConnector should be of type Connector"

    # get query target options for data sources
    chronicle_query_target_options = await connector.get_query_target_options()
    assert isinstance(chronicle_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select data sources to target
    data_source_selector = None
    for selector in chronicle_query_target_options.selectors:
        if selector.type == 'data_source_ids':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"

    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    data_source_id = data_source_selector.values[0] if data_source_selector.values else None
    print(f"Selecting data source ID: {data_source_id}")

    assert data_source_id, f"failed to retrieve data source ID from data source selector"

    # set up the target with data source ID
    target = ChronicleTarget(data_source_ids=[data_source_id])
    assert isinstance(target, ConnectorTargetInterface), "ChronicleTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the execute_udm_search tool
    execute_udm_search_tool = next(tool for tool in tools if tool.name == "execute_udm_search")
    
    # Test UDM search execution
    search_result = await execute_udm_search_tool.execute(
        query='metadata.event_type = "NETWORK_CONNECTION" AND principal.ip = /192\.168\..*/',
        start_time="2024-01-01T00:00:00Z",
        end_time="2024-01-01T23:59:59Z",
        max_results=100
    )
    search_results = search_result.result

    print("Type of returned search results:", type(search_results))
    print(f"Search results data: {str(search_results)[:300]}")

    # Verify that search_results is a dictionary with expected structure
    assert isinstance(search_results, dict), "search_results should be a dictionary"
    
    # Verify essential search result fields
    assert "events" in search_results, "Search results should have an 'events' field"
    assert "moreDataAvailable" in search_results, "Search results should have a 'moreDataAvailable' field"
    
    # Verify events structure
    events = search_results["events"]
    assert isinstance(events, list), "events should be a list"
    
    if len(events) > 0:
        # Check structure of events
        first_event = events[0]
        assert isinstance(first_event, dict), "Each event should be a dictionary"
        assert "metadata" in first_event, "Each event should have metadata"
        
        # Verify UDM event structure
        metadata = first_event["metadata"]
        udm_fields = ["event_timestamp", "event_type", "product_name"]
        present_udm_fields = [field for field in udm_fields if field in metadata]
        
        print(f"UDM search results contain events with these metadata fields: {', '.join(present_udm_fields)}")
    
    # Test search pagination if available
    if "get_search_results" in [tool.name for tool in tools] and search_results.get("moreDataAvailable"):
        get_search_results_tool = next(tool for tool in tools if tool.name == "get_search_results")
        next_page_result = await get_search_results_tool.execute(
            page_token=search_results.get("nextPageToken", "")
        )
        next_page_data = next_page_result.result
        
        if next_page_data:
            assert isinstance(next_page_data, dict), "Next page data should be a dictionary"
            assert "events" in next_page_data, "Next page data should have events"
            
            print(f"Retrieved next page with {len(next_page_data['events'])} additional events")
    
    # Test analytics generation if available
    if "generate_security_analytics" in [tool.name for tool in tools]:
        generate_analytics_tool = next(tool for tool in tools if tool.name == "generate_security_analytics")
        analytics_result = await generate_analytics_tool.execute(
            data_source_id=data_source_id,
            time_period="24h",
            event_types=["NETWORK_CONNECTION", "USER_LOGIN"]
        )
        analytics_data = analytics_result.result
        
        if analytics_data:
            assert isinstance(analytics_data, dict), "Analytics data should be a dictionary"
            
            # Verify analytics structure
            analytics_fields = ["event_summary", "top_assets", "network_analytics", "security_insights"]
            present_analytics_fields = [field for field in analytics_fields if field in analytics_data]
            
            print(f"Security analytics contains these sections: {', '.join(present_analytics_fields)}")
            
            # Verify event summary if present
            if "event_summary" in analytics_data:
                event_summary = analytics_data["event_summary"]
                assert isinstance(event_summary, dict), "event_summary should be a dictionary"
                
                summary_fields = ["total_events", "unique_assets", "event_type_distribution"]
                present_summary_fields = [field for field in summary_fields if field in event_summary]
                
                print(f"Event summary contains: {', '.join(present_summary_fields)}")
    
    # Test rule execution if available
    if "execute_detection_rule" in [tool.name for tool in tools]:
        execute_rule_tool = next(tool for tool in tools if tool.name == "execute_detection_rule")
        rule_result = await execute_rule_tool.execute(
            rule_text='rule test_rule { meta: description = "Test rule" events: $e.metadata.event_type = "NETWORK_CONNECTION" condition: $e }',
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-01T23:59:59Z"
        )
        rule_data = rule_result.result
        
        if rule_data:
            assert isinstance(rule_data, dict), "Rule execution result should be a dictionary"
            
            rule_fields = ["detections", "rule_id", "compilation_state"]
            present_rule_fields = [field for field in rule_fields if field in rule_data]
            
            print(f"Rule execution contains: {', '.join(present_rule_fields)}")
    
    # Test asset timeline if available
    if "get_asset_timeline" in [tool.name for tool in tools]:
        get_timeline_tool = next(tool for tool in tools if tool.name == "get_asset_timeline")
        timeline_result = await get_timeline_tool.execute(
            asset_identifier="192.168.1.1",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-01T23:59:59Z"
        )
        timeline_data = timeline_result.result
        
        if timeline_data:
            assert isinstance(timeline_data, list), "Timeline data should be a list"
            
            if len(timeline_data) > 0:
                first_timeline_event = timeline_data[0]
                assert isinstance(first_timeline_event, dict), "Each timeline event should be a dictionary"
                
                print(f"Asset timeline contains {len(timeline_data)} events")
    
    # Log the structure of the search results for debugging
    print(f"Example UDM search results structure: {search_results}")
    
    # Verify more data available flag
    more_data_available = search_results["moreDataAvailable"]
    assert isinstance(more_data_available, bool), "moreDataAvailable should be a boolean"
    
    print(f"Successfully executed UDM search with {len(events)} events (more data available: {more_data_available})")

    return True