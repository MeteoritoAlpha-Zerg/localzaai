# 5-test_list_retrieval.py

async def test_list_retrieval(zerg_state=None):
    """Test Trello list retrieval by way of connector tools"""
    print("Attempting to authenticate using Trello connector")

    assert zerg_state, "this test requires valid zerg_state"

    trello_api_key = zerg_state.get("trello_api_key").get("value")
    trello_api_token = zerg_state.get("trello_api_token").get("value")
    trello_url = zerg_state.get("trello_url").get("value")

    from connectors.trello.config import TrelloConnectorConfig
    from connectors.trello.connector import TrelloConnector
    from connectors.trello.tools import TrelloConnectorTools, GetTrelloListsInput
    from connectors.trello.target import TrelloTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = TrelloConnectorConfig(
        api_key=trello_api_key,
        api_token=trello_api_token,
        url=trello_url,
    )
    assert isinstance(config, ConnectorConfig), "TrelloConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = TrelloConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TrelloConnector should be of type Connector"

    # get query target options
    trello_query_target_options = await connector.get_query_target_options()
    assert isinstance(trello_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select boards to target
    board_selector = None
    for selector in trello_query_target_options.selectors:
        if selector.type == 'board_ids':  
            board_selector = selector
            break

    assert board_selector, "failed to retrieve board selector from query target options"

    assert isinstance(board_selector.values, list), "board_selector values must be a list"
    board_id = board_selector.values[0] if board_selector.values else None
    print(f"Selecting board id: {board_id}")

    assert board_id, f"failed to retrieve board id from board selector"

    # set up the target with board id
    target = TrelloTarget(board_ids=[board_id])
    assert isinstance(target, ConnectorTargetInterface), "TrelloTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_trello_lists tool and execute it with board id
    get_trello_lists_tool = next(tool for tool in tools if tool.name == "get_trello_lists")
    trello_lists_result = await get_trello_lists_tool.execute(board_id=board_id)
    trello_lists = trello_lists_result.result

    print("Type of returned trello_lists:", type(trello_lists))
    print(f"len lists: {len(trello_lists)} lists: {str(trello_lists)[:200]}")

    # Verify that trello_lists is a list
    assert isinstance(trello_lists, list), "trello_lists should be a list"
    assert len(trello_lists) > 0, "trello_lists should not be empty"
    
    # Limit the number of lists to check if there are many
    lists_to_check = trello_lists[:5] if len(trello_lists) > 5 else trello_lists
    
    # Verify structure of each list object
    for trello_list in lists_to_check:
        # Verify essential Trello list fields
        assert "id" in trello_list, "Each list should have an 'id' field"
        assert "name" in trello_list, "Each list should have a 'name' field"
        
        # Verify the list belongs to the requested board
        assert "idBoard" in trello_list, "Each list should have an 'idBoard' field"
        assert trello_list["idBoard"] == board_id, f"List {trello_list['id']} does not belong to the requested board_id"
        
        # Check for additional descriptive fields (common in Trello lists)
        optional_fields = ["closed", "pos", "subscribed", "softLimit", "type"]
        present_optional = [field for field in optional_fields if field in trello_list]
        
        print(f"List {trello_list['id']} ({trello_list['name']}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first list for debugging
        if trello_list == lists_to_check[0]:
            print(f"Example list structure: {trello_list}")

    # Display information about the first list
    first_list = trello_lists[0]
    list_id = first_list.get('id', 'No id found')
    list_name = first_list.get('name', 'No name found')

    print(f"First Trello list for board {board_id}: {list_id} - {list_name}")

    print(f"Successfully retrieved and validated {len(trello_lists)} Trello lists for board {board_id}")

    return True