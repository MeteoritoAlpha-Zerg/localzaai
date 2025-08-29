# 6-test_page_content_retrieval.py

async def test_page_content_retrieval(zerg_state=None):
    """Test Confluence page content retrieval"""
    print("Attempting to retrieve page content using Confluence connector")

    assert zerg_state, "this test requires valid zerg_state"

    def truncate_str(s, max_length=200):
        s = str(s)
        return s[:max_length] + ("..." if len(s) > max_length else "")

    confluence_url = zerg_state.get("confluence_url").get("value")
    confluence_api_token = zerg_state.get("confluence_api_token").get("value")
    confluence_email = zerg_state.get("confluence_email").get("value")

    from connectors.confluence.config import ConfluenceConnectorConfig
    from connectors.confluence.connector import ConfluenceConnector
    from connectors.confluence.tools import ConfluenceConnectorTools
    from connectors.confluence.target import ConfluenceTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # Set up the config
    config = ConfluenceConnectorConfig(
        url=confluence_url,
        api_token=confluence_api_token,
        email=confluence_email
    )
    assert isinstance(config, ConnectorConfig), "ConfluenceConnectorConfig should be of type ConnectorConfig"

    # Set up the connector
    connector = ConfluenceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ConfluenceConnector should be of type Connector"

    # First, get a space and then a page
    confluence_query_target_options = await connector.get_query_target_options()
    assert isinstance(confluence_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"
    
    space_selector = None
    for selector in confluence_query_target_options.selectors:
        if selector.type == 'space_keys':  
            space_selector = selector
            break

    assert space_selector, "failed to retrieve space selector from query target options"

    # Grab the first space for now
    assert isinstance(space_selector.values, list), "space_selector values must be a list"
    space_key = space_selector.values[0] if space_selector.values else None
    print(f"Selecting space key: {space_key}")

    assert space_key, "failed to retrieve space key from space selector"
    
    # Set up the target with space key
    target = ConfluenceTarget(space_keys=[space_key])
    assert isinstance(target, ConnectorTargetInterface), "ConfluenceTarget should be of type ConnectorTargetInterface"

    # Get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # Grab the get_confluence_pages tool
    confluence_get_pages_tool = next(tool for tool in tools if tool.name == "get_confluence_pages")
    confluence_pages_result = await confluence_get_pages_tool.execute(space_key=space_key)
    confluence_pages = confluence_pages_result.result
    
    # Verify the pages were retrieved successfully
    assert isinstance(confluence_pages, list), "confluence_pages should be a list"
    assert len(confluence_pages) > 0, "confluence_pages should not be empty"
    
    # Get the first page to test content retrieval
    first_page = confluence_pages[0]
    assert first_page, f"No Confluence pages found for space {space_key}"
    
    page_id = first_page.get('id')
    assert page_id, "Page ID is missing from the retrieved page"
    page_title = first_page.get('title', 'No title found')
    print(f"Selected page for content retrieval: {page_id} - {page_title}")
    
    # Grab the get_confluence_page_content tool
    confluence_get_page_content_tool = next(tool for tool in tools if tool.name == "get_confluence_page_content")
    
    # Call the tool with the page_id parameter
    page_content_result = await confluence_get_page_content_tool.execute(page_id=page_id)
    page_content = page_content_result.result
    
    # Verify content was retrieved
    assert page_content, f"No content found for page {page_id}"
    
    # Check content type and structure
    assert isinstance(page_content, str), "Page content should be a string"
    assert len(page_content) > 0, "Page content should not be empty"
    
    # Get a preview of the content for logging
    content_preview = page_content[:100] + "..." if len(page_content) > 100 else page_content
    print(f"Content preview from page {page_id}: {truncate_str(content_preview)}")
    
    # Check if content contains expected HTML elements
    common_html_elements = ["<p>", "<div", "<span", "<h", "<a", "<table"]
    found_elements = [element for element in common_html_elements if element in page_content]
    
    if found_elements:
        print(f"Content contains HTML elements: {', '.join(found_elements)}")
    else:
        print("Content does not contain common HTML elements, may be in storage format or plain text")
    
    print(f"Successfully retrieved content for page {page_id} in space {space_key}")
    
    return True