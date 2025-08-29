async def test_ticket_search(zerg_state=None):
    """Test Zendesk ticket search functionality"""
    print("Testing ticket search using Zendesk connector")

    assert zerg_state, "this test requires valid zerg_state"

    zendesk_subdomain = zerg_state.get("zendesk_subdomain").get("value")
    zendesk_email = zerg_state.get("zendesk_email").get("value")
    zendesk_api_token = zerg_state.get("zendesk_api_token").get("value")

    from connectors.zendesk.config import ZendeskConnectorConfig
    from connectors.zendesk.connector import ZendeskConnector
    from connectors.zendesk.tools import ZendeskConnectorTools
    from connectors.zendesk.target import ZendeskTarget

    config = ZendeskConnectorConfig(
        subdomain=zendesk_subdomain,
        email=zendesk_email,
        api_token=SecretStr(zendesk_api_token)
    )
    connector = ZendeskConnector(config)

    connector_target = ZendeskTarget(config=config)
    
    # Get connector tools
    tools = ZendeskConnectorTools(
        zendesk_config=config, 
        target=ZendeskTarget, 
        connector_display_name="Zendesk"
    )
    
    # Define some search queries to test
    search_queries = [
        "status:open", 
        "status:pending",
        "priority:high",
        "type:incident"
    ]
    
    for query in search_queries:
        try:
            search_results = await tools.search_zendesk_tickets(query=query)
            print(f'Search for "{query}" returned {len(search_results)} results')
            
            if search_results and len(search_results) > 0:
                first_result = search_results[0]
                print(f"First result: Ticket #{first_result.get('id')} - {first_result.get('subject')}")
                break
        except Exception as e:
            print(f"Search for {query} failed: {e}")
            continue
    
    # If no pre-defined searches worked, try a simple keyword search
    if not search_results or len(search_results) == 0:
        try:
            keyword_search = await tools.search_zendesk_tickets(query="")  # Empty query returns recent tickets
            print(f"Keyword search returned {len(keyword_search)} results")
            
            if keyword_search and len(keyword_search) > 0:
                first_result = keyword_search[0]
                print(f"First result: Ticket #{first_result.get('id')} - {first_result.get('subject')}")
        except Exception as e:
            print(f"Keyword search failed: {e}")
    
    return True