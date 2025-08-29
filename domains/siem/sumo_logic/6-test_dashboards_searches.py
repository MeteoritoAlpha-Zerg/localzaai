# 6-test_dashboards_searches.py

async def test_dashboards_searches(zerg_state=None):
    """Test Sumo Logic dashboards and saved searches retrieval"""
    print("Attempting to retrieve dashboards and searches using Sumo Logic connector")

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

    # Test 1: Get dashboards
    get_sumologic_dashboards_tool = next(tool for tool in tools if tool.name == "get_sumologic_dashboards")
    sumologic_dashboards_result = await get_sumologic_dashboards_tool.execute(limit=10)
    sumologic_dashboards = sumologic_dashboards_result.result

    print("Type of returned sumologic_dashboards:", type(sumologic_dashboards))
    print(f"len dashboards: {len(sumologic_dashboards)} dashboards: {str(sumologic_dashboards)[:200]}")

    assert isinstance(sumologic_dashboards, list), "sumologic_dashboards should be a list"
    
    if len(sumologic_dashboards) > 0:
        dashboards_to_check = sumologic_dashboards[:3] if len(sumologic_dashboards) > 3 else sumologic_dashboards
        
        for dashboard in dashboards_to_check:
            assert "id" in dashboard, "Each dashboard should have an 'id' field"
            assert "title" in dashboard, "Each dashboard should have a 'title' field"
            assert "type" in dashboard, "Each dashboard should have a 'type' field"
            
            optional_fields = ["description", "folderId", "createdBy", "modifiedBy", "panels"]
            present_optional = [field for field in optional_fields if field in dashboard]
            
            print(f"Dashboard {dashboard['title']} contains these optional fields: {', '.join(present_optional)}")
            
            if dashboard == dashboards_to_check[0]:
                print(f"Example dashboard structure: {dashboard}")

        print(f"Successfully retrieved and validated {len(sumologic_dashboards)} Sumo Logic dashboards")
    else:
        print("No dashboards found - this is acceptable for testing")

    # Test 2: Get saved searches
    get_sumologic_saved_searches_tool = next(tool for tool in tools if tool.name == "get_sumologic_saved_searches")
    sumologic_saved_searches_result = await get_sumologic_saved_searches_tool.execute(limit=10)
    sumologic_saved_searches = sumologic_saved_searches_result.result

    print("Type of returned sumologic_saved_searches:", type(sumologic_saved_searches))
    print(f"len saved searches: {len(sumologic_saved_searches)} searches: {str(sumologic_saved_searches)[:200]}")

    assert isinstance(sumologic_saved_searches, list), "sumologic_saved_searches should be a list"
    
    if len(sumologic_saved_searches) > 0:
        searches_to_check = sumologic_saved_searches[:3] if len(sumologic_saved_searches) > 3 else sumologic_saved_searches
        
        for search in searches_to_check:
            assert "id" in search, "Each saved search should have an 'id' field"
            assert "name" in search, "Each saved search should have a 'name' field"
            assert "query" in search, "Each saved search should have a 'query' field"
            
            optional_fields = ["description", "timeRange", "byReceiptTime", "queryParameters"]
            present_optional = [field for field in optional_fields if field in search]
            
            print(f"Saved search {search['name']} contains these optional fields: {', '.join(present_optional)}")

        print(f"Successfully retrieved and validated {len(sumologic_saved_searches)} Sumo Logic saved searches")
    else:
        print("No saved searches found - this is acceptable for testing")

    # Test 3: Get content folders
    get_sumologic_folders_tool = next(tool for tool in tools if tool.name == "get_sumologic_folders")
    sumologic_folders_result = await get_sumologic_folders_tool.execute()
    sumologic_folders = sumologic_folders_result.result

    print("Type of returned sumologic_folders:", type(sumologic_folders))

    assert isinstance(sumologic_folders, list), "sumologic_folders should be a list"
    
    if len(sumologic_folders) > 0:
        folders_to_check = sumologic_folders[:3] if len(sumologic_folders) > 3 else sumologic_folders
        
        for folder in folders_to_check:
            assert "id" in folder, "Each folder should have an 'id' field"
            assert "name" in folder, "Each folder should have a 'name' field"
            assert "itemType" in folder, "Each folder should have an 'itemType' field"
            
            print(f"Folder {folder['name']} is of type {folder['itemType']}")

        print(f"Successfully retrieved and validated {len(sumologic_folders)} Sumo Logic folders")

    print("Successfully completed dashboards and saved searches tests")

    return True