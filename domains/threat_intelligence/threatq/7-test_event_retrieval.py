# 7-test_event_retrieval.py

async def test_event_retrieval(zerg_state=None):
    """Test ThreatQ event information retrieval"""
    print("Attempting to authenticate using ThreatQ connector")

    assert zerg_state, "this test requires valid zerg_state"

    threatq_api_host = zerg_state.get("threatq_api_host").get("value")
    threatq_api_path = zerg_state.get("threatq_api_path").get("value")
    threatq_username = zerg_state.get("threatq_username").get("value")
    threatq_password = zerg_state.get("threatq_password").get("value")
    threatq_client_id = zerg_state.get("threatq_client_id").get("value")

    from connectors.threatq.config import ThreatQConnectorConfig
    from connectors.threatq.connector import ThreatQConnector
    from connectors.threatq.target import ThreatQTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ThreatQConnectorConfig(
        api_host=threatq_api_host,
        api_path=threatq_api_path,
        username=threatq_username,
        password=threatq_password,
        client_id=threatq_client_id
    )
    assert isinstance(config, ConnectorConfig), "ThreatQConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ThreatQConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ThreatQConnector should be of type Connector"

    # get query target options
    threatq_query_target_options = await connector.get_query_target_options()
    assert isinstance(threatq_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # set up the target
    target = ThreatQTarget()
    assert isinstance(target, ConnectorTargetInterface), "ThreatQTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Find the get_events tool
    get_events_tool = next((tool for tool in tools if tool.name == "get_events"), None)
    assert get_events_tool is not None, "get_events tool not found"
    
    # Test 1: Get all events with pagination
    print("\nTest 1: Retrieving events with pagination...")
    events_result = await get_events_tool.execute(
        limit=10,  # Limit to 10 for testing
        offset=0,
        with_attributes=True,  # Include attributes
        with_sources=True,     # Include sources
        with_indicators=True   # Include related indicators
    )
    events = events_result.result

    print("Type of returned events data:", type(events))
    
    # Verify the events data structure
    assert isinstance(events, list), "events should be a list"
    
    # Check if we found any events
    if len(events) > 0:
        print(f"Found {len(events)} events")
        
        # Check event fields for the first event
        event = events[0]
        print("\nSample Event Details:")
        print(f"ID: {event.get('id')}")
        print(f"Title: {event.get('title', 'N/A')}")
        print(f"Type: {event.get('type', 'N/A')}")
        print(f"Status: {event.get('status', 'N/A')}")
        
        # Check for essential fields
        essential_fields = ["id"]
        for field in essential_fields:
            assert field in event, f"Event missing essential field: {field}"
        
        # Check for common metadata fields
        common_fields = ["title", "type", "status", "created_at", "updated_at", "happened_at", "description"]
        present_fields = [field for field in common_fields if field in event]
        print(f"Present metadata fields: {', '.join(present_fields)}")
        
        for field in present_fields:
            print(f"{field.replace('_', ' ').title()}: {event.get(field, 'N/A')}")
        
        # Check for attributes if available
        if "attributes" in event and event["attributes"]:
            print("\nAttributes:")
            assert isinstance(event["attributes"], list), "attributes should be a list"
            for attr in event["attributes"]:
                assert "name" in attr, "Attribute missing 'name' field"
                assert "value" in attr, "Attribute missing 'value' field"
                print(f"  {attr['name']}: {attr['value']}")
        
        # Check for sources if available
        if "sources" in event and event["sources"]:
            print("\nSources:")
            assert isinstance(event["sources"], list), "sources should be a list"
            for source in event["sources"]:
                assert "name" in source, "Source missing 'name' field"
                print(f"  {source['name']}")
        
        # Check for indicators if available
        if "indicators" in event and event["indicators"]:
            print("\nRelated Indicators:")
            assert isinstance(event["indicators"], list), "indicators should be a list"
            for indicator in event["indicators"][:5]:  # Show up to 5 indicators
                assert "value" in indicator, "Indicator missing 'value' field"
                assert "type" in indicator, "Indicator missing 'type' field"
                print(f"  {indicator['type']}: {indicator['value']}")
        
        # Now get a specific event by ID for detailed testing
        event_id = event["id"]
        print(f"\nTest 2: Retrieving details for specific event ID: {event_id}")
        
        # Find the get_event_by_id tool
        get_event_by_id_tool = next((tool for tool in tools if tool.name == "get_event_by_id"), None)
        
        if get_event_by_id_tool:
            event_detail_result = await get_event_by_id_tool.execute(
                event_id=event_id,
                with_attributes=True,
                with_sources=True,
                with_indicators=True
            )
            event_detail = event_detail_result.result
            
            # Verify the detailed event data structure
            assert isinstance(event_detail, dict), "event_detail should be a dict"
            assert event_detail["id"] == event_id, "Returned event ID doesn't match requested ID"
            
            print("\nDetailed Event Information:")
            print(f"ID: {event_detail['id']}")
            if "title" in event_detail:
                print(f"Title: {event_detail['title']}")
            if "type" in event_detail:
                print(f"Type: {event_detail['type']}")
            if "status" in event_detail:
                print(f"Status: {event_detail['status']}")
            if "happened_at" in event_detail:
                print(f"Happened At: {event_detail['happened_at']}")
            if "description" in event_detail:
                print(f"Description: {event_detail['description']}")
                
            # Check additional relationships that might be in the detailed view
            for related_type in ["indicators", "attributes", "sources", "adversaries"]:
                if related_type in event_detail and event_detail[related_type]:
                    print(f"\nRelated {related_type.capitalize()}:")
                    count = len(event_detail[related_type])
                    print(f"  Found {count} related {related_type}")
                    
                    # Show examples of related items
                    for i, item in enumerate(event_detail[related_type][:3]):  # Limit to 3 items for readability
                        if related_type == "indicators":
                            print(f"  {i+1}. {item.get('type', 'Unknown')}: {item.get('value', 'N/A')}")
                        elif related_type == "attributes":
                            print(f"  {i+1}. {item.get('name', 'Unknown')}: {item.get('value', 'N/A')}")
                        elif related_type == "sources":
                            print(f"  {i+1}. {item.get('name', 'Unknown')}")
                        elif related_type == "adversaries":
                            print(f"  {i+1}. {item.get('name', 'Unknown')}")
        else:
            print("get_event_by_id tool not found, skipping detailed event retrieval test")
    else:
        print("No events found in the ThreatQ instance")
        
        # Test 3: Try to search for events by type if no events found initially
        print("\nTest 3: Searching for events by type...")
        event_types = ["Malware", "Phishing", "Data Breach", "Incident", "Campaign"]
        
        found_events_by_type = False
        for event_type in event_types:
            events_by_type_result = await get_events_tool.execute(
                limit=5,
                offset=0,
                type=event_type
            )
            events_by_type = events_by_type_result.result
            
            if events_by_type:
                found_events_by_type = True
                print(f"Found {len(events_by_type)} events of type '{event_type}'")
                
                # Show a sample event of this type
                sample_event = events_by_type[0]
                print(f"\nSample {event_type} event:")
                print(f"ID: {sample_event.get('id')}")
                print(f"Title: {sample_event.get('title', 'N/A')}")
                print(f"Status: {sample_event.get('status', 'N/A')}")
                if "happened_at" in sample_event:
                    print(f"Happened At: {sample_event['happened_at']}")
                
                break
        
        if not found_events_by_type:
            print("No events found for any of the common event types")

    print("\nSuccessfully completed event retrieval test")
    return True