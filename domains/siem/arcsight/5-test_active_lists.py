# 5-test_active_lists.py

async def test_active_lists(zerg_state=None):
    """Test ArcSight active list data retrieval"""
    print("Attempting to retrieve active lists using ArcSight connector")

    assert zerg_state, "this test requires valid zerg_state"

    arcsight_server_url = zerg_state.get("arcsight_server_url").get("value")
    arcsight_username = zerg_state.get("arcsight_username").get("value")
    arcsight_password = zerg_state.get("arcsight_password").get("value")

    from connectors.arcsight.config import ArcSightConnectorConfig
    from connectors.arcsight.connector import ArcSightConnector
    from connectors.arcsight.tools import ArcSightConnectorTools, GetActiveListDataInput
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

    # get query target options
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

    # grab the get_active_list_data tool and execute it
    get_active_list_data_tool = next(tool for tool in tools if tool.name == "get_active_list_data")
    active_list_data_result = await get_active_list_data_tool.execute(security_manager_id=security_manager_id)
    active_list_data = active_list_data_result.result

    print("Type of returned active_list_data:", type(active_list_data))
    print(f"len active lists: {len(active_list_data)} lists: {str(active_list_data)[:200]}")

    # Verify that active_list_data is a list
    assert isinstance(active_list_data, list), "active_list_data should be a list"
    assert len(active_list_data) > 0, "active_list_data should not be empty"
    
    # Limit the number of active lists to check if there are many
    lists_to_check = active_list_data[:5] if len(active_list_data) > 5 else active_list_data
    
    # Verify structure of each active list object
    for active_list in lists_to_check:
        # Verify essential ArcSight active list fields
        assert "uri" in active_list, "Each active list should have a 'uri' field"
        assert "name" in active_list, "Each active list should have a 'name' field"
        assert "type" in active_list, "Each active list should have a 'type' field"
        
        # Verify common ArcSight active list fields
        assert "columns" in active_list, "Each active list should have a 'columns' field"
        assert "entryCount" in active_list, "Each active list should have an 'entryCount' field"
        
        # Check for additional optional fields
        optional_fields = ["description", "createdTimestamp", "modifiedTimestamp", "ttl"]
        present_optional = [field for field in optional_fields if field in active_list]
        
        print(f"Active list {active_list['name']} (entries: {active_list['entryCount']}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first active list for debugging
        if active_list == lists_to_check[0]:
            print(f"Example active list structure: {active_list}")

    # Test retrieving entries from a specific active list if tool is available
    if "get_active_list_entries" in [tool.name for tool in tools]:
        get_entries_tool = next(tool for tool in tools if tool.name == "get_active_list_entries")
        
        # Use the first active list
        first_list_uri = active_list_data[0]["uri"]
        entries_result = await get_entries_tool.execute(active_list_uri=first_list_uri)
        entries_data = entries_result.result
        
        if entries_data:
            assert isinstance(entries_data, list), "Active list entries should be a list"
            
            if len(entries_data) > 0:
                # Check structure of entries
                first_entry = entries_data[0]
                assert isinstance(first_entry, dict), "Each entry should be a dictionary"
                
                print(f"Retrieved {len(entries_data)} entries from active list {active_list_data[0]['name']}")

    print(f"Successfully retrieved and validated {len(active_list_data)} ArcSight active lists")

    return True