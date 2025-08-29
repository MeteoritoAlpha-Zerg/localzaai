# 5-test_page_retrieval.py

async def test_page_retrieval(zerg_state=None):
    """Test Confluence page retrieval for a selected space"""
    print("Attempting to authenticate using Confluence connector")

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
    
    # set up the config
    config = ConfluenceConnectorConfig(
        url=confluence_url,
        api_token=confluence_api_token,
        email=confluence_email
    )
    assert isinstance(config, ConnectorConfig), "ConfluenceConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ConfluenceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ConfluenceConnector should be of type Connector"

    # get query target options
    confluence_query_target_options = await connector.get_query_target_options()
    assert isinstance(confluence_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    print(f"confluence query target option definitions: {truncate_str(confluence_query_target_options.definitions)}")
    print(f"confluence query target option selectors: {truncate_str(confluence_query_target_options.selectors)}")

    # select spaces to target
    space_selector = None
    for selector in confluence_query_target_options.selectors:
        if selector.type == 'space_keys':  
            space_selector = selector
            break

    assert space_selector, "failed to retrieve space selector from query target options"

    # grab the first space for now
    assert isinstance(space_selector.values, list), "space_selector values must be a list"
    space_key = space_selector.values[0] if space_selector.values else None
    print(f"Selecting space key: {space_key}")

    assert space_key, "failed to retrieve space key from space selector"

    # set up the target with space key
    target = ConfluenceTarget(space_keys=[space_key])
    assert isinstance(target, ConnectorTargetInterface), "ConfluenceTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_confluence_pages tool
    confluence_get_pages_tool = next(tool for tool in tools if tool.name == "get_confluence_pages")
    confluence_pages_result = await confluence_get_pages_tool.execute(space_key=space_key)
    confluence_pages = confluence_pages_result.result

    print("Type of returned confluence_pages:", type(confluence_pages))
    print(f"len pages: {len(confluence_pages)} pages: {str(confluence_pages)[:200]}")

    # ensure that confluence_pages are a list of objects with proper structure
    # Verify that confluence_pages is a list
    assert isinstance(confluence_pages, list), "confluence_pages should be a list"
    assert len(confluence_pages) > 0, "confluence_pages should not be empty"
    
    # Verify structure of each page object
    for page in confluence_pages:
        assert "id" in page, "Each page should have an 'id' field"
        assert "title" in page, "Each page should have a 'title' field"
        
        # Check for additional descriptive fields (optional in some Confluence instances)
        descriptive_fields = ["spaceKey", "url", "self", "version", "parentId", "status"]
        present_fields = [field for field in descriptive_fields if field in page]
        
        print(f"Page {page['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Check if the page belongs to the specified space
        assert "spaceKey" in page or "_expandable" in page, "Each page should have space information"
        if "spaceKey" in page:
            assert page["spaceKey"] == space_key, f"Page space key {page['spaceKey']} does not match the requested space key {space_key}"
        
        # Log the full structure of the first page
        if page == confluence_pages[0]:
            print(f"Example page structure: {truncate_str(page, 400)}")

    print(f"Successfully retrieved and validated {len(confluence_pages)} Confluence pages for space {space_key}")

    return True