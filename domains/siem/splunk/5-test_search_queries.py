# 5-test_search_queries.py

async def test_search_queries(zerg_state=None):
    """Test Splunk search query execution"""
    print("Testing Splunk search query execution")

    assert zerg_state, "this test requires valid zerg_state"

    splunk_host = zerg_state.get("splunk_host").get("value")
    splunk_port = zerg_state.get("splunk_port").get("value")
    splunk_username = zerg_state.get("splunk_username").get("value")
    splunk_password = zerg_state.get("splunk_password").get("value")
    splunk_hec_token = zerg_state.get("splunk_hec_token").get("value")

    from connectors.splunk.config import SplunkConnectorConfig
    from connectors.splunk.connector import SplunkConnector
    from connectors.splunk.target import SplunkTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SplunkConnectorConfig(
        host=splunk_host,
        port=int(splunk_port),
        username=splunk_username,
        password=splunk_password,
        hec_token=splunk_hec_token
    )
    assert isinstance(config, ConnectorConfig), "SplunkConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SplunkConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SplunkConnector should be of type Connector"

    # get query target options
    splunk_query_target_options = await connector.get_query_target_options()
    assert isinstance(splunk_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select index to target
    index_selector = None
    for selector in splunk_query_target_options.selectors:
        if selector.type == 'index_names':  
            index_selector = selector
            break

    assert index_selector, "failed to retrieve index selector from query target options"

    assert isinstance(index_selector.values, list), "index_selector values must be a list"
    index_name = index_selector.values[0] if index_selector.values else None
    print(f"Selecting index name: {index_name}")

    assert index_name, f"failed to retrieve index name from index selector"

    # set up the target with index name
    target = SplunkTarget(index_names=[index_name])
    assert isinstance(target, ConnectorTargetInterface), "SplunkTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the execute_search_query tool and execute it with index name
    execute_search_tool = next(tool for tool in tools if tool.name == "execute_search_query")
    
    # Create a simple SPL search query to test functionality
    test_search_query = f"search index={index_name} | head 10"  # Simple query to get some results
    
    search_result = await execute_search_tool.execute(
        index_name=index_name,
        search_query=test_search_query,
        earliest_time="-1h",  # Last hour
        latest_time="now"
    )
    search_results = search_result.result

    print("Type of returned search_results:", type(search_results))
    print(f"Search results preview: {str(search_results)[:200]}")

    # Verify that search_results contains structured data
    assert search_results is not None, "search_results should not be None"
    
    # Search results could be a list of events or a dictionary with metadata
    if isinstance(search_results, list):
        # If we have results, verify their structure
        if len(search_results) > 0:
            # Limit the number of results to check
            results_to_check = search_results[:3] if len(search_results) > 3 else search_results
            
            for result in results_to_check:
                # Each result should be a dictionary representing a Splunk event
                assert isinstance(result, dict), "Each search result should be a dictionary"
                
                # Common Splunk fields that might be present
                common_fields = ["_time", "_raw", "_indextime", "_sourcetype", "index", "source", "host"]
                present_common = [field for field in common_fields if field in result]
                
                print(f"Splunk event contains these common fields: {', '.join(present_common)}")
                
                # Verify _time field format if present
                if "_time" in result:
                    time_field = result["_time"]
                    assert isinstance(time_field, (str, int, float)), "Time field should be string or numeric"
                
                # Verify _raw field if present (contains original log data)
                if "_raw" in result:
                    raw_field = result["_raw"]
                    assert isinstance(raw_field, str), "Raw field should be a string"
                
                # Verify index field matches target if present
                if "index" in result:
                    assert result["index"] == index_name, f"Event index should match target index {index_name}"
                
                # Log the structure of the first result for debugging
                if result == results_to_check[0]:
                    print(f"Example search result structure: {result}")
        else:
            print("No search results returned - this is acceptable if index is empty or query matches no data")
            
    elif isinstance(search_results, dict):
        # Results might be wrapped in metadata structure
        expected_keys = ["events", "results", "messages", "preview"]
        has_data_key = any(key in search_results for key in expected_keys)
        
        if has_data_key:
            print(f"Search results contain metadata with keys: {list(search_results.keys())}")
            
            # Check the actual events/results
            for key in expected_keys:
                if key in search_results and key in ["events", "results"]:
                    events = search_results[key]
                    if isinstance(events, list):
                        print(f"Found {len(events)} events in {key}")
                        
                        # Verify event structure if we have events
                        if len(events) > 0:
                            sample_event = events[0]
                            assert isinstance(sample_event, dict), "Each event should be a dictionary"
                    break
            
            # Check for messages or errors
            if "messages" in search_results:
                messages = search_results["messages"]
                print(f"Search messages: {messages}")
        else:
            # Could be error information or other metadata
            print(f"Search results metadata keys: {list(search_results.keys())}")
    
    else:
        # Results could be in other formats, just ensure it's not empty
        assert str(search_results).strip() != "", "Search results should not be empty"

    print(f"Successfully executed SPL search query and retrieved results")

    return True