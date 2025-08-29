# 4-test_list_spaces.py

async def test_list_spaces(zerg_state=None):
    """Test Confluence space enumeration by way of query target options"""
    print("Attempting to authenticate using Confluence connector")

    assert zerg_state, "this test requires valid zerg_state"

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

    # select spaces to target
    space_selector = None
    for selector in confluence_query_target_options.selectors:
        if selector.type == 'space_keys':  
            space_selector = selector
            break

    assert space_selector, "failed to retrieve space selector from query target options"

    # grab the first space for now
    #num_spaces = 1
    assert isinstance(space_selector.values, list), "space_selector values must be a list"
    space_key = space_selector.values[0] if space_selector.values else None
    print(f"Selecting space key: {space_key}")

    assert space_key, "failed to retrieve space key from space selector"

    # set up the target with space keys
    target = ConfluenceTarget(space_keys=[space_key])
    assert isinstance(target, ConnectorTargetInterface), "ConfluenceTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_confluence_spaces tool
    confluence_get_spaces_tool = next(tool for tool in tools if tool.name == "get_confluence_spaces")
    confluence_spaces_result = await confluence_get_spaces_tool.execute()
    confluence_spaces = confluence_spaces_result.result

    print("Type of returned confluence_spaces:", type(confluence_spaces))
    print(f"len spaces: {len(confluence_spaces)} spaces: {str(confluence_spaces)[:200]}")

    # ensure that confluence_spaces are a list of objects with the key being the space key
    # and the object having the space description and other relevant information from the confluence specification
    # as may be descriptive
    # Verify that confluence_spaces is a list
    assert isinstance(confluence_spaces, list), "confluence_spaces should be a list"
    assert len(confluence_spaces) > 0, "confluence_spaces should not be empty"
    #assert len(confluence_spaces) == num_spaces, f"confluence_spaces should have {num_spaces} entries"
    
    # Verify structure of each space object
    for space in confluence_spaces:
        assert "key" in space, "Each space should have a 'key' field"
        assert space["key"] in [space_key], f"Space key {space['key']} is not in the requested space_keys"
        
        # Verify essential Confluence space fields
        # These are common fields in Confluence spaces based on Confluence API specification
        assert "id" in space, "Each space should have an 'id' field"
        assert "name" in space, "Each space should have a 'name' field"
        
        # Check for additional descriptive fields (optional in some Confluence instances)
        descriptive_fields = ["description", "type", "url", "self"]
        present_fields = [field for field in descriptive_fields if field in space]
        
        print(f"Space {space['key']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first space
        if space == confluence_spaces[0]:
            print(f"Example space structure: {space}")

    print(f"Successfully retrieved and validated {len(confluence_spaces)} Confluence spaces")

    return True