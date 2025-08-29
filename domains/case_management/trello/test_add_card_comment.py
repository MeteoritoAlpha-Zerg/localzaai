async def test_add_card_comment(zerg_state=None):
    """Test adding a comment to a Trello card"""
    print("Attempting to add a comment to a card using Trello connector")

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

    # First get a board, then a list, then a card
    trello_query_target_options = await connector.get_query_target_options()
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
    
    connector_target.board_id = board_id
    
    # Get connector tools
    tools = TrelloConnectorTools(
        trello_config=config, 
        target=TrelloTarget, 
        connector_display_name="Trello"
    )
    
    # Get lists from this board
    trello_lists = await tools.get_trello_lists()
    first_list = trello_lists[0] if trello_lists else None
    assert first_list, f"No Trello lists found for board {board_id}"
    
    list_id = first_list.get('id')
    connector_target.list_id = list_id
    
    # Get cards from this list
    cards = await tools.get_trello_cards()
    assert cards and len(cards) > 0, f"No cards found in list {first_list.get('name')}"
    
    # Select the first card
    first_card = cards[0]
    card_id = first_card.get('id')
    card_name = first_card.get('name')
    
    # Add a comment to the card
    import time
    timestamp = int(time.time())
    comment_text = f"Test comment added by connector test at {timestamp}"
    
    comment = await tools.add_comment_to_card(
        card_id=card_id,
        text=comment_text
    )
    
    assert comment, "Failed to add comment to card"
    assert comment.get('id'), "Comment response does not have an ID"
    assert comment.get('data', {}).get('text') == comment_text, "Comment text does not match requested text"
    
    print(f"Successfully added comment to card '{card_name}'")
    
    return True