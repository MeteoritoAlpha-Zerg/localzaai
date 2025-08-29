# 4-test_list_groups.py

async def test_list_groups(zerg_state=None):
    """Test Signal group enumeration by way of query target options"""
    print("Attempting to authenticate using Signal connector")

    assert zerg_state, "this test requires valid zerg_state"

    signal_api_url = zerg_state.get("signal_api_url").get("value")
    signal_phone_number = zerg_state.get("signal_phone_number").get("value")
    signal_api_key = zerg_state.get("signal_api_key").get("value")

    from connectors.signal.config import SignalConnectorConfig
    from connectors.signal.connector import SignalConnector
    from connectors.signal.tools import SignalConnectorTools
    from connectors.signal.target import SignalTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = SignalConnectorConfig(
        api_url=signal_api_url,
        phone_number=signal_phone_number,
        api_key=signal_api_key
    )
    assert isinstance(config, ConnectorConfig), "SignalConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SignalConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SignalConnectorConfig should be of type ConnectorConfig"

    # get query target options
    signal_query_target_options = await connector.get_query_target_options()
    assert isinstance(signal_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select groups to target
    group_selector = None
    for selector in signal_query_target_options.selectors:
        if selector.type == 'group_ids':  
            group_selector = selector
            break

    assert group_selector, "failed to retrieve group selector from query target options"

    # grab the first two groups 
    num_groups = 2
    assert isinstance(group_selector.values, list), "group_selector values must be a list"
    group_ids = group_selector.values[:num_groups] if group_selector.values else None
    print(f"Selecting group ids: {group_ids}")

    assert group_ids, f"failed to retrieve {num_groups} group ids from group selector"

    # set up the target with group ids
    target = SignalTarget(group_ids=group_ids)
    assert isinstance(target, ConnectorTargetInterface), "SignalTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_signal_groups tool
    signal_get_groups_tool = next(tool for tool in tools if tool.name == "get_signal_groups")
    signal_groups_result = await signal_get_groups_tool.execute()
    signal_groups = signal_groups_result.result

    print("Type of returned signal_groups:", type(signal_groups))
    print(f"len groups: {len(signal_groups)} groups: {str(signal_groups)[:200]}")

    # ensure that signal_groups are a list of objects with the id being the group id
    # and the object having the group name and other relevant information from the signal specification
    # as may be descriptive
    # Verify that signal_groups is a list
    assert isinstance(signal_groups, list), "signal_groups should be a list"
    assert len(signal_groups) > 0, "signal_groups should not be empty"
    assert len(signal_groups) == num_groups, f"signal_groups should have {num_groups} entries"
    
    # Verify structure of each group object
    for group in signal_groups:
        assert "id" in group, "Each group should have an 'id' field"
        assert group["id"] in group_ids, f"Group id {group['id']} is not in the requested group_ids"
        
        # Verify essential Signal group fields
        # These are common fields in Signal groups based on Signal API specification
        assert "name" in group, "Each group should have a 'name' field"
        
        # Check for additional descriptive fields (optional in some Signal instances)
        descriptive_fields = ["description", "members", "admins", "created_at", "avatar"]
        present_fields = [field for field in descriptive_fields if field in group]
        
        print(f"Group {group['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if group == signal_groups[0]:
            print(f"Example group structure: {group}")

    print(f"Successfully retrieved and validated {len(signal_groups)} Signal groups")

    return True