async def test_create_card(zerg_state=None):
    """Test Trello card creation"""
    print("Attempting to create a card using Trello connector")

    assert zerg_state, "this test requires valid zerg_state"

    trello_api_key = zerg_state.get("trello_api_key").get("value")
    trello_api_token = zerg_state.get("trello_api_token").get("value")

    from connectors.trello.config import TrelloConnectorConfig
    from connectors.trello.connector import TrelloConnector
    from connectors.trello.tools import TrelloConnectorTools
    from connectors.trello.target import TrelloTarget

    config = TrelloConnectorConfig(
        api_key=trello_api_key,
        api_token=SecretStr(trello_api_token),
        url="https://api.trello.com"
    )
    connector = TrelloConnector(config)

    connector_target = TrelloTarget(config=config)

    # First get a board and then a list
    trello_query_target_options = await connector.get_query_target_options()
    assert trello_query_target_options, "Failed to retrieve query target options"
    
    board_selector = None
    for selector in trello_query_target_options.selectors:
        if selector.type == 'board':  
            board_selector = selector
            break

    assert board_selector, "failed to retrieve board selector from query target options"

    if board_selector:
        if isinstance(board_selector.values, list):
            board_id = board_selector.values[0] if board_selector.values else None
        else:  
            board_id = list(board_selector.values.keys())[0] if board_selector.values else None

    assert board_id, "failed to retrieve board id from board selector"
    
    # set board_id in target
    connector_target.board_id = board_id
    
    # Get lists from this board
    tools = TrelloConnectorTools(
        trello_config=config, 
        target=TrelloTarget, 
        connector_display_name="Trello"
    )
    
    trello_lists = await tools.get_trello_lists()
    
    first_list = trello_lists[0] if trello_lists else None
    assert first_list, f"No Trello lists found for board {board_id}"
    
    list_id = first_list.get('id')
    connector_target.list_id = list_id
    
    # Create a test card with a unique name
    import time
    timestamp = int(time.time())
    card_name = f"Test Card - {timestamp}"
    card_description = "This is a test card created by the Trello connector test"
    
    new_card = await tools.create_trello_card(
        name=card_name,
        description=card_description
    )
    
    assert new_card, "Failed to create new card"
    assert new_card.get('id'), "New card does not have an ID"
    assert new_card.get('name') == card_name, "New card name does not match requested name"
    
    card_id = new_card.get('id')
    print(f"Successfully created card '{card_name}' in list '{first_list.get('name')}'")
    
    # Store the card ID for later cleanup or reference
    # This would be implemented in a real test environment
    
    return True