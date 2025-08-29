# 6-test_knowledge_base_query.py

async def test_knowledge_base_query(zerg_state=None):
    """Test SysAid knowledge base query by way of connector tools"""
    print("Testing knowledge base query using SysAid connector")

    assert zerg_state, "this test requires valid zerg_state"

    sysaid_url = zerg_state.get("sysaid_url").get("value")
    sysaid_account_id = zerg_state.get("sysaid_account_id").get("value")
    sysaid_username = zerg_state.get("sysaid_username").get("value")
    sysaid_password = zerg_state.get("sysaid_password").get("value")

    from connectors.sysaid.config import SysAidConnectorConfig
    from connectors.sysaid.connector import SysAidConnector
    from connectors.sysaid.tools import SysAidConnectorTools, GetSysAidKnowledgeBaseArticlesInput
    from connectors.sysaid.target import SysAidTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SysAidConnectorConfig(
        url=sysaid_url,
        account_id=sysaid_account_id,
        username=sysaid_username,
        password=sysaid_password,
    )
    assert isinstance(config, ConnectorConfig), "SysAidConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SysAidConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SysAidConnector should be of type Connector"

    # set up the target (knowledge base queries don't typically need specific targeting)
    target = SysAidTarget()
    assert isinstance(target, ConnectorTargetInterface), "SysAidTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_sysaid_knowledge_base_articles tool and execute it
    get_kb_articles_tool = next(tool for tool in tools if tool.name == "get_sysaid_knowledge_base_articles")
    kb_articles_result = await get_kb_articles_tool.execute(limit=10)
    kb_articles = kb_articles_result.result

    print("Type of returned kb_articles:", type(kb_articles))
    print(f"len articles: {len(kb_articles)} articles: {str(kb_articles)[:200]}")

    # Verify that kb_articles is a list
    assert isinstance(kb_articles, list), "kb_articles should be a list"
    assert len(kb_articles) > 0, "kb_articles should not be empty"
    
    # Limit the number of articles to check if there are many
    articles_to_check = kb_articles[:5] if len(kb_articles) > 5 else kb_articles
    
    # Verify structure of each knowledge base article object
    for article in articles_to_check:
        # Verify essential SysAid knowledge base article fields
        assert "id" in article, "Each article should have an 'id' field"
        assert "title" in article, "Each article should have a 'title' field"
        
        # Check for additional descriptive fields (common in SysAid knowledge base articles)
        optional_fields = ["content", "category", "subcategory", "tags", "author", "createDate", "modifyDate", "viewCount", "rating", "status", "keywords"]
        present_optional = [field for field in optional_fields if field in article]
        
        print(f"Article {article['id']} ({article['title'][:50]}...) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first article for debugging
        if article == articles_to_check[0]:
            print(f"Example article structure: {article}")

    # Display information about the first few articles
    for i, article in enumerate(articles_to_check[:3]):
        print(f"Article {i+1}:")
        print(f"  ID: {article.get('id')}")
        print(f"  Title: {article.get('title')}")
        print(f"  Category: {article.get('category')}")
        print(f"  Last Updated: {article.get('modifyDate')}")

    # Test search functionality if available
    try:
        search_kb_tool = next(tool for tool in tools if tool.name == "search_sysaid_knowledge_base")
        search_term = "security"
        search_result = await search_kb_tool.execute(query=search_term)
        security_articles = search_result.result
        
        print(f"Found {len(security_articles)} articles matching search term '{search_term}'")
        
        if security_articles:
            print(f"Top search result: {security_articles[0].get('title')}")
            
        # Verify search results structure
        assert isinstance(security_articles, list), "search results should be a list"
        for search_article in security_articles[:2]:  # Check first 2 search results
            assert "id" in search_article, "Each search result should have an 'id' field"
            assert "title" in search_article, "Each search result should have a 'title' field"
            
    except StopIteration:
        print("Search knowledge base tool not available - skipping search test")

    print(f"Successfully retrieved and validated {len(kb_articles)} SysAid knowledge base articles")

    return True