def truncate_str(s, max_length=200):
    s = str(s)
    return s[:max_length] + ("..." if len(s) > max_length else "")

async def test_security_content_search(zerg_state=None):
    """Test Confluence security content search capabilities"""
    print("Searching for security-related content using Confluence connector")

    assert zerg_state, "this test requires valid zerg_state"

    confluence_url = zerg_state.get("confluence_url").get("value")
    confluence_api_token = zerg_state.get("confluence_api_token").get("value")
    confluence_email = zerg_state.get("confluence_email").get("value")

    from connectors.confluence.config import ConfluenceConnectorConfig
    from connectors.confluence.connector import ConfluenceConnector
    from connectors.confluence.tools import ConfluenceConnectorTools
    from connectors.confluence.target import ConfluenceTarget

    config = ConfluenceConnectorConfig(
        url=confluence_url,
        api_token=SecretStr(confluence_api_token),
        email=confluence_email
    )
    connector = ConfluenceConnector(config)

    connector_target = ConfluenceTarget(config=config)

    # Get connector tools
    tools = ConfluenceConnectorTools(
        confluence_config=config, 
        target=ConfluenceTarget, 
        connector_display_name="Confluence"
    )
    
    # Define security-related search terms
    security_terms = ["security policy", "vulnerability", "risk assessment", 
                        "incident response", "compliance", "data breach", 
                        "security controls", "cyber", "authentication"]
    
    # Search for each term
    all_security_results = []
    for term in security_terms:
        security_results = await tools.search_confluence_content(query=term)
        if security_results:
            all_security_results.extend(security_results)
    
    # Get unique results (may have duplicates from different search terms)
    unique_result_ids = set()
    unique_results = []
    
    for result in all_security_results:
        if result.get('id') not in unique_result_ids:
            unique_result_ids.add(result.get('id'))
            unique_results.append(result)
    
    print(f"Found {len(unique_results)} unique security-related content items in Confluence")
    
    if unique_results:
        sample_result = unique_results[0]
        print(f"Sample security content: {sample_result.get('title')} - {truncate_str(sample_result.get('space'))}")
    
    return True