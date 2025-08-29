def truncate_str(s, max_length=200):
    s = str(s)
    return s[:max_length] + ("..." if len(s) > max_length else "")

async def test_security_policy_extraction(zerg_state=None):
    """Test Confluence security policy extraction capabilities"""
    print("Extracting security policies using Confluence connector")

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
    
    # Specifically search for security policy pages
    policy_results = await tools.search_confluence_content(query="security policy")
    
    if not policy_results:
        print("No security policy documents found")
        # To avoid test failure in case there are no actual security policies in the instance
        return True
        
    # Extract the first policy document for analysis
    policy_page_id = policy_results[0].get('id')
    policy_content = await tools.get_confluence_page_content(page_id=policy_page_id)
    
    # Now use the specialized extraction tool
    policy_structure = await tools.extract_security_policy_structure(page_content=policy_content)
    
    # Check if structure was extracted
    assert policy_structure, "Failed to extract structured policy information"
    
    # Print some details about the extracted policy
    print(f"Extracted security policy structure from page {policy_page_id}")
    print(f"Policy categories: {', '.join(policy_structure.get('categories', []))}")
    print(f"Policy version: {policy_structure.get('version', 'Unknown')}")
    print(f"Last updated: {policy_structure.get('last_updated', 'Unknown')}")
    
    return True