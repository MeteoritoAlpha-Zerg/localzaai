# 6-test_card_retrieval.py

async def test_card_retrieval(zerg_state=None):
    """Test Trello card retrieval by way of connector tools"""
    print("Attempting to retrieve cards using Trello connector")

    assert zerg_state, "this test requires valid zerg_state"

    trello_api_key = zerg_state.get("trello_api_key").get("value")
    trello_api_token = zerg_state.get("trello_api_token").get("value")
    trello_url = zerg_state.get("trello_url").get("value")

    from connectors.trello.config import TrelloConnectorConfig
    from connectors.trello.connector import TrelloConnector
    from connectors.trello.tools import TrelloConnectorTools, GetTrelloCardsInput
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

    # set up the target with board id to get lists
    target = TrelloTarget(board_ids=[board_id])
    assert isinstance(target, ConnectorTargetInterface), "TrelloTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # get lists from this board first
    get_trello_lists_tool = next(tool for tool in tools if tool.name == "get_trello_lists")
    trello_lists_result = await get_trello_lists_tool.execute(board_id=board_id)
    trello_lists = trello_lists_result.result

    assert isinstance(trello_lists, list), "trello_lists should be a list"
    assert len(trello_lists) > 0, "trello_lists should not be empty"

    # select the first list
    first_list = trello_lists[0]
    list_id = first_list.get('id')
    list_name = first_list.get('name', 'Unknown')
    
    print(f"Using list: {list_id} - {list_name}")

    # now get cards from this list
    get_trello_cards_tool = next(tool for tool in tools if tool.name == "get_trello_cards")
    trello_cards_result = await get_trello_cards_tool.execute(list_id=list_id)
    trello_cards = trello_cards_result.result

    print("Type of returned trello_cards:", type(trello_cards))
    print(f"len cards: {len(trello_cards)} cards: {str(trello_cards)[:200]}")

    # Verify that trello_cards is a list
    assert isinstance(trello_cards, list), "trello_cards should be a list"
    assert len(trello_cards) >= 0, "trello_cards should be a valid list (can be empty)"
    
    if len(trello_cards) > 0:
        # Limit the number of cards to check if there are many
        cards_to_check = trello_cards[:5] if len(trello_cards) > 5 else trello_cards
        
        # Verify structure of each card object
        for card in cards_to_check:
            # Verify essential Trello card fields
            assert "id" in card, "Each card should have an 'id' field"
            assert "name" in card, "Each card should have a 'name' field"
            
            # Verify the card belongs to the requested list
            assert "idList" in card, "Each card should have an 'idList' field"
            assert card["idList"] == list_id, f"Card {card['id']} does not belong to the requested list_id"
            
            # Check for additional descriptive fields (common in Trello cards)
            optional_fields = ["desc", "closed", "pos", "url", "shortUrl", "idBoard", "dateLastActivity", "labels", "idMembers", "due", "dueComplete"]
            present_optional = [field for field in optional_fields if field in card]
            
            print(f"Card {card['id']} ({card['name']}) contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first card for debugging
            if card == cards_to_check[0]:
                print(f"Example card structure: {card}")

        # Display information about the first card
        first_card = trello_cards[0]
        card_name = first_card.get('name', 'Unknown')
        card_id = first_card.get('id', 'Unknown')
        
        print(f"First card: {card_id} - {card_name}")

        print(f"Successfully retrieved and validated {len(trello_cards)} Trello cards from list {list_name}")
    else:
        print(f"List {list_name} contains no cards - this is valid")

    return True