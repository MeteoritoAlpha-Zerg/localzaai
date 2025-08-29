# 6-test_security_search.py

async def test_security_search(zerg_state=None):
    """Test ArcSight security search and analytics functionality"""
    print("Attempting to execute security searches using ArcSight connector")

    assert zerg_state, "this test requires valid zerg_state"

    arcsight_server_url = zerg_state.get("arcsight_server_url").get("value")
    arcsight_username = zerg_state.get("arcsight_username").get("value")
    arcsight_password = zerg_state.get("arcsight_password").get("value")

    from connectors.arcsight.config import ArcSightConnectorConfig
    from connectors.arcsight.connector import ArcSightConnector
    from connectors.arcsight.tools import ArcSightConnectorTools, ExecuteSecuritySearchInput
    from connectors.arcsight.target import ArcSightTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ArcSightConnectorConfig(
        server_url=arcsight_server_url,
        username=arcsight_username,
        password=arcsight_password
    )
    assert isinstance(config, ConnectorConfig), "ArcSightConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ArcSightConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ArcSightConnector should be of type Connector"

    # get query target options for security managers
    arcsight_query_target_options = await connector.get_query_target_options()
    assert isinstance(arcsight_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select security managers to target
    security_manager_selector = None
    for selector in arcsight_query_target_options.selectors:
        if selector.type == 'security_manager_ids':  
            security_manager_selector = selector
            break

    assert security_manager_selector, "failed to retrieve security manager selector from query target options"

    assert isinstance(security_manager_selector.values, list), "security_manager_selector values must be a list"
    security_manager_id = security_manager_selector.values[0] if security_manager_selector.values else None
    print(f"Selecting security manager ID: {security_manager_id}")

    assert security_manager_id, f"failed to retrieve security manager ID from security manager selector"

    # set up the target with security manager ID
    target = ArcSightTarget(security_manager_ids=[security_manager_id])
    assert isinstance(target, ConnectorTargetInterface), "ArcSightTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the execute_security_search tool
    execute_security_search_tool = next(tool for tool in tools if tool.name == "execute_security_search")
    
    # Test security search execution
    search_result = await execute_security_search_tool.execute(
        query="type = \"Base Event\" AND priority >= 5",
        time_range="LAST_24_HOURS",
        max_results=100
    )
    search_results = search_result.result

    print("Type of returned search results:", type(search_results))
    print(f"Search results data: {str(search_results)[:300]}")

    # Verify that search_results is a dictionary with expected structure
    assert isinstance(search_results, dict), "search_results should be a dictionary"
    
    # Verify essential search result fields
    assert "searchSessionId" in search_results, "Search results should have a 'searchSessionId' field"
    assert "status" in search_results, "Search results should have a 'status' field"
    assert "events" in search_results, "Search results should have an 'events' field"
    
    # Verify events structure
    events = search_results["events"]
    assert isinstance(events, list), "events should be a list"
    
    if len(events) > 0:
        # Check structure of events
        first_event = events[0]
        assert isinstance(first_event, dict), "Each event should be a dictionary"
        
        # Verify common event fields
        event_fields = ["eventId", "startTime", "name", "priority"]
        present_event_fields = [field for field in event_fields if field in first_event]
        
        print(f"Search results contain events with these fields: {', '.join(present_event_fields)}")
    
    # Test search status if available
    if "get_search_status" in [tool.name for tool in tools]:
        get_search_status_tool = next(tool for tool in tools if tool.name == "get_search_status")
        status_result = await get_search_status_tool.execute(
            search_session_id=search_results["searchSessionId"]
        )
        status_data = status_result.result
        
        if status_data:
            assert isinstance(status_data, dict), "Status data should be a dictionary"
            assert "status" in status_data, "Status data should have a 'status' field"
            
            print(f"Search status: {status_data['status']}")
    
    # Test analytics generation if available
    if "generate_security_analytics" in [tool.name for tool in tools]:
        generate_analytics_tool = next(tool for tool in tools if tool.name == "generate_security_analytics")
        analytics_result = await generate_analytics_tool.execute(
            security_manager_id=security_manager_id,
            time_period="24h",
            event_types=["Base Event", "Correlation Event"]
        )
        analytics_data = analytics_result.result
        
        if analytics_data:
            assert isinstance(analytics_data, dict), "Analytics data should be a dictionary"
            
            # Verify analytics structure
            analytics_fields = ["event_summary", "top_sources", "top_destinations", "threat_analysis"]
            present_analytics_fields = [field for field in analytics_fields if field in analytics_data]
            
            print(f"Security analytics contains these sections: {', '.join(present_analytics_fields)}")
            
            # Verify event summary if present
            if "event_summary" in analytics_data:
                event_summary = analytics_data["event_summary"]
                assert isinstance(event_summary, dict), "event_summary should be a dictionary"
                
                summary_fields = ["total_events", "high_priority_events", "correlation_events"]
                present_summary_fields = [field for field in summary_fields if field in event_summary]
                
                print(f"Event summary contains: {', '.join(present_summary_fields)}")
    
    # Test correlation analysis if available
    if "get_correlation_analysis" in [tool.name for tool in tools]:
        get_correlation_tool = next(tool for tool in tools if tool.name == "get_correlation_analysis")
        correlation_result = await get_correlation_tool.execute(
            security_manager_id=security_manager_id,
            time_range="LAST_6_HOURS"
        )
        correlation_data = correlation_result.result
        
        if correlation_data:
            assert isinstance(correlation_data, dict), "Correlation data should be a dictionary"
            
            correlation_fields = ["correlation_events", "patterns", "anomalies"]
            present_correlation_fields = [field for field in correlation_fields if field in correlation_data]
            
            print(f"Correlation analysis contains: {', '.join(present_correlation_fields)}")
    
    # Log the structure of the search results for debugging
    print(f"Example search results structure: {search_results}")
    
    # Verify search session ID format
    search_session_id = search_results["searchSessionId"]
    assert isinstance(search_session_id, str), "searchSessionId should be a string"
    assert len(search_session_id) > 0, "searchSessionId should not be empty"
    
    print(f"Successfully executed security search with session ID: {search_session_id}")

    return True