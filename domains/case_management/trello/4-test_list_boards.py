# 4-test_list_boards.py

async def test_list_boards(zerg_state=None):
    """Test Trello board enumeration by way of connector tools"""
    print("Attempting to authenticate using Trello connector")

    assert zerg_state, "this test requires valid zerg_state"

    trello_api_key = zerg_state.get("trello_api_key").get("value")
    trello_api_token = zerg_state.get("trello_api_token").get("value")
    trello_url = zerg_state.get("trello_url").get("value")

    from connectors.trello.config import TrelloConnectorConfig
    from connectors.trello.connector import TrelloConnector
    from connectors.trello.tools import TrelloConnectorTools
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

    # grab the first two boards 
    num_boards = 2
    assert isinstance(board_selector.values, list), "board_selector values must be a list"
    board_ids = board_selector.values[:num_boards] if board_selector.values else None
    print(f"Selecting board ids: {board_ids}")

    assert board_ids, f"failed to retrieve {num_boards} board ids from board selector"

    # set up the target with board ids
    target = TrelloTarget(board_ids=board_ids)
    assert isinstance(target, ConnectorTargetInterface), "TrelloTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_trello_boards tool
    trello_get_boards_tool = next(tool for tool in tools if tool.name == "get_trello_boards")
    trello_boards_result = await trello_get_boards_tool.execute()
    trello_boards = trello_boards_result.result

    print("Type of returned trello_boards:", type(trello_boards))
    print(f"len boards: {len(trello_boards)} boards: {str(trello_boards)[:200]}")

    # ensure that trello_boards are a list of objects with the id being the board id
    # and the object having the board description and other relevant information from the trello specification
    # as may be descriptive
    # Verify that trello_boards is a list
    assert isinstance(trello_boards, list), "trello_boards should be a list"
    assert len(trello_boards) > 0, "trello_boards should not be empty"
    assert len(trello_boards) == num_boards, f"trello_boards should have {num_boards} entries"
    
    # Verify structure of each board object
    for board in trello_boards:
        assert "id" in board, "Each board should have an 'id' field"
        assert board["id"] in board_ids, f"Board id {board['id']} is not in the requested board_ids"
        
        # Verify essential Trello board fields
        # These are common fields in Trello boards based on Trello API specification
        assert "name" in board, "Each board should have a 'name' field"
        assert "url" in board, "Each board should have a 'url' field"
        
        # Check for additional descriptive fields (optional in some Trello instances)
        descriptive_fields = ["desc", "closed", "prefs", "dateLastActivity", "dateLastView", "shortUrl", "starred", "pinned", "powerUps", "subscribed"]
        present_fields = [field for field in descriptive_fields if field in board]
        
        print(f"Board {board['id']} ({board['name']}) contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if board == trello_boards[0]:
            print(f"Example board structure: {board}")

    print(f"Successfully retrieved and validated {len(trello_boards)} Trello boards")

    return True