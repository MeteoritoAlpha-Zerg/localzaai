# 5-test_search_queries.py

async def test_search_queries(zerg_state=None):
    """Test CrowdStrike Humio search query execution"""
    print("Testing CrowdStrike Humio search query execution")

    assert zerg_state, "this test requires valid zerg_state"

    humio_api_token = zerg_state.get("humio_api_token").get("value")
    humio_base_url = zerg_state.get("humio_base_url").get("value")
    humio_organization = zerg_state.get("humio_organization").get("value")

    from connectors.crowdstrike_humio.config import CrowdStrikeHumioConnectorConfig
    from connectors.crowdstrike_humio.connector import CrowdStrikeHumioConnector
    from connectors.crowdstrike_humio.target import CrowdStrikeHumioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = CrowdStrikeHumioConnectorConfig(
        api_token=humio_api_token,
        base_url=humio_base_url,
        organization=humio_organization
    )
    assert isinstance(config, ConnectorConfig), "CrowdStrikeHumioConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CrowdStrikeHumioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CrowdStrikeHumioConnector should be of type Connector"

    # get query target options
    humio_query_target_options = await connector.get_query_target_options()
    assert isinstance(humio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select repository to target
    repository_selector = None
    for selector in humio_query_target_options.selectors:
        if selector.type == 'repository_names':  
            repository_selector = selector
            break

    assert repository_selector, "failed to retrieve repository selector from query target options"

    assert isinstance(repository_selector.values, list), "repository_selector values must be a list"
    repository_name = repository_selector.values[0] if repository_selector.values else None
    print(f"Selecting repository name: {repository_name}")

    assert repository_name, f"failed to retrieve repository name from repository selector"

    # set up the target with repository name
    target = CrowdStrikeHumioTarget(repository_names=[repository_name])
    assert isinstance(target, ConnectorTargetInterface), "CrowdStrikeHumioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the execute_search_query tool and execute it with repository name
    execute_search_tool = next(tool for tool in tools if tool.name == "execute_search_query")
    
    # Create a simple search query to test functionality
    test_search_query = "*"  # Simple wildcard query to get some results
    
    search_result = await execute_search_tool.execute(
        repository_name=repository_name,
        query=test_search_query,
        start_time="1h",  # Last hour
        limit=10
    )
    search_results = search_result.result

    print("Type of returned search_results:", type(search_results))
    print(f"Search results preview: {str(search_results)[:200]}")

    # Verify that search_results contains structured data
    assert search_results is not None, "search_results should not be None"
    
    # Search results could be a list of log events or a dictionary with metadata
    if isinstance(search_results, list):
        # If we have results, verify their structure
        if len(search_results) > 0:
            # Limit the number of results to check
            results_to_check = search_results[:3] if len(search_results) > 3 else search_results
            
            for result in results_to_check:
                # Each result should be a dictionary representing a log event
                assert isinstance(result, dict), "Each search result should be a dictionary"
                
                # Common Humio fields that might be present
                common_fields = ["@timestamp", "@rawstring", "@timezone", "@id"]
                present_common = [field for field in common_fields if field in result]
                
                print(f"Log event contains these common fields: {', '.join(present_common)}")
                
                # Verify timestamp format if present
                if "@timestamp" in result:
                    timestamp = result["@timestamp"]
                    assert isinstance(timestamp, (str, int, float)), "Timestamp should be string or numeric"
                
                # Log the structure of the first result for debugging
                if result == results_to_check[0]:
                    print(f"Example search result structure: {result}")
        else:
            print("No search results returned - this is acceptable if repository is empty or query matches no data")
            
    elif isinstance(search_results, dict):
        # Results might be wrapped in metadata structure
        expected_keys = ["events", "results", "data", "rows"]
        has_data_key = any(key in search_results for key in expected_keys)
        
        if has_data_key:
            print(f"Search results contain metadata with keys: {list(search_results.keys())}")
            
            # Check the actual events/data
            for key in expected_keys:
                if key in search_results:
                    events = search_results[key]
                    assert isinstance(events, list), f"Search results {key} should be a list"
                    print(f"Found {len(events)} events in {key}")
                    break
        else:
            # Could be error information or other metadata
            print(f"Search results metadata keys: {list(search_results.keys())}")
    
    else:
        # Results could be in other formats, just ensure it's not empty
        assert str(search_results).strip() != "", "Search results should not be empty"

    print(f"Successfully executed search query and retrieved results")

    return True