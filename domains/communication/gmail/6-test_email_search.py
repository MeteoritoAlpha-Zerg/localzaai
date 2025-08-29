# 6-test_email_search.py

async def test_email_search(zerg_state=None):
    """Test Gmail email search and filtering by way of connector tools"""
    print("Attempting to authenticate using Gmail connector")

    assert zerg_state, "this test requires valid zerg_state"

    # Config setup
    gmail_oauth_client_id = zerg_state.get("gmail_oauth_client_id").get("value")
    gmail_oauth_client_secret = zerg_state.get("gmail_oauth_client_secret").get("value")
    gmail_oauth_refresh_token = zerg_state.get("gmail_oauth_refresh_token").get("value")
    gmail_api_base_url = zerg_state.get("gmail_api_base_url").get("value")
    gmail_api_version = zerg_state.get("gmail_api_version").get("value")

    from connectors.gmail.config import GmailConnectorConfig
    from connectors.gmail.connector import GmailConnector
    from connectors.gmail.target import GmailTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    config = GmailConnectorConfig(
        oauth_client_id=gmail_oauth_client_id, oauth_client_secret=gmail_oauth_client_secret,
        oauth_refresh_token=gmail_oauth_refresh_token, api_base_url=gmail_api_base_url, api_version=gmail_api_version
    )

    connector = GmailConnector
    await connector.initialize(config=config, user_id="test_user_id", encryption_key="test_enc_key")

    # Set up target for searching
    target = GmailTarget(label_ids=["INBOX"])  # Search in INBOX
    tools = await connector.get_tools(target=target)
    search_email_tool = next(tool for tool in tools if tool.name == "search_gmail_messages")
    
    # Test different search scenarios
    search_scenarios = [
        {"query": "is:unread", "description": "unread messages"},
        {"query": "from:gmail.com", "description": "messages from Gmail domain"},
        {"query": "newer_than:7d", "description": "messages from last 7 days"},
    ]
    
    for scenario in search_scenarios:
        query = scenario["query"]
        description = scenario["description"]
        
        print(f"Testing search for {description} with query: {query}")
        
        search_result = await search_email_tool.execute(
            query=query,
            max_results=20
        )
        search_messages = search_result.result

        print("Type of returned search_messages:", type(search_messages))
        print(f"Search for '{description}' returned {len(search_messages)} messages")

        # Validate search results
        assert isinstance(search_messages, list), "search_messages should be a list"
        
        # Search might return no results, which is valid
        if len(search_messages) > 0:
            for message in search_messages[:3]:  # Check first 3 results
                assert "id" in message, "Each search result should have an 'id' field"
                assert "threadId" in message, "Each search result should have a 'threadId' field"
                
                # Check for snippet (Gmail search usually returns snippets)
                if "snippet" in message:
                    snippet = message["snippet"]
                    assert isinstance(snippet, str), "Snippet should be a string"
                    print(f"Message {message['id']} snippet: {snippet[:50]}...")
                
                # Check for label IDs
                if "labelIds" in message:
                    label_ids = message["labelIds"]
                    assert isinstance(label_ids, list), "Label IDs should be a list"
        
        # Brief delay between search queries
        import asyncio
        await asyncio.sleep(0.1)

    print("Successfully validated Gmail email search functionality")
    return True