# 5-test_search_execution.py

async def test_search_execution(zerg_state=None):
    """Test Sumo Logic search query execution and log data retrieval"""
    print("Attempting to execute searches using Sumo Logic connector")

    assert zerg_state, "this test requires valid zerg_state"

    sumologic_url = zerg_state.get("sumologic_url").get("value")
    sumologic_access_id = zerg_state.get("sumologic_access_id").get("value")
    sumologic_access_key = zerg_state.get("sumologic_access_key").get("value")

    from connectors.sumologic.config import SumoLogicConnectorConfig
    from connectors.sumologic.connector import SumoLogicConnector
    from connectors.sumologic.tools import SumoLogicConnectorTools
    from connectors.sumologic.target import SumoLogicTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = SumoLogicConnectorConfig(
        url=sumologic_url,
        access_id=sumologic_access_id,
        access_key=sumologic_access_key,
    )
    assert isinstance(config, ConnectorConfig), "SumoLogicConnectorConfig should be of type ConnectorConfig"

    connector = SumoLogicConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SumoLogicConnector should be of type Connector"

    sumologic_query_target_options = await connector.get_query_target_options()
    assert isinstance(sumologic_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    collector_selector = None
    for selector in sumologic_query_target_options.selectors:
        if selector.type == 'collector_ids':  
            collector_selector = selector
            break

    assert collector_selector, "failed to retrieve collector selector from query target options"

    assert isinstance(collector_selector.values, list), "collector_selector values must be a list"
    collector_id = collector_selector.values[0] if collector_selector.values else None
    print(f"Selecting collector ID: {collector_id}")

    assert collector_id, f"failed to retrieve collector ID from collector selector"

    target = SumoLogicTarget(collector_ids=[collector_id])
    assert isinstance(target, ConnectorTargetInterface), "SumoLogicTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    execute_sumologic_search_tool = next(tool for tool in tools if tool.name == "execute_sumologic_search")
    
    # Use a basic Sumo Logic search query
    test_query = f"_sourceCategory=* | limit 100"
    
    sumologic_search_result = await execute_sumologic_search_tool.execute(
        query=test_query,
        from_time="2024-01-01T00:00:00Z",
        to_time="2024-12-31T23:59:59Z",
        timeout=300
    )
    sumologic_search_data = sumologic_search_result.result

    print("Type of returned sumologic_search_data:", type(sumologic_search_data))
    print(f"len search results: {len(sumologic_search_data)} results: {str(sumologic_search_data)[:200]}")

    assert isinstance(sumologic_search_data, list), "sumologic_search_data should be a list"
    assert len(sumologic_search_data) > 0, "sumologic_search_data should not be empty"
    
    results_to_check = sumologic_search_data[:5] if len(sumologic_search_data) > 5 else sumologic_search_data
    
    for result in results_to_check:
        assert isinstance(result, dict), "Each result should be a dictionary"
        
        common_fields = ["_messageTime", "_raw", "_sourceCategory", "_sourceHost", "_sourceName"]
        present_common = [field for field in common_fields if field in result]
        
        print(f"Search result contains these common fields: {', '.join(present_common)}")
        
        if result == results_to_check[0]:
            print(f"Example search result structure: {result}")

    print(f"Successfully executed Sumo Logic search and validated {len(sumologic_search_data)} results")

    return True