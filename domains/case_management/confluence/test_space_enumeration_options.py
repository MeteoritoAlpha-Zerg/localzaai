def truncate_str(s, max_length=200):
    s = str(s)
    return s[:max_length] + ("..." if len(s) > max_length else "")

async def test_space_enumeration_options(zerg_state=None):
    """Test Confluence space enumeration by way of query target options"""
    print("Attempting to authenticate using Confluence connector")

    assert zerg_state, "this test requires valid zerg_state"

    confluence_url = zerg_state.get("confluence_url").get("value")
    confluence_api_token = zerg_state.get("confluence_api_token").get("value")
    confluence_email = zerg_state.get("confluence_email").get("value")

    from connectors.confluence.config import ConfluenceConnectorConfig
    from connectors.confluence.connector import ConfluenceConnector
    from connectors.confluence.target import ConfluenceTarget

    config = ConfluenceConnectorConfig(
        url=confluence_url,
        api_token=SecretStr(confluence_api_token),
        email=confluence_email
    )
    connector = ConfluenceConnector(config)

    connector_target = ConfluenceTarget(config=config)

    confluence_query_target_options = await connector.get_query_target_options()

    assert confluence_query_target_options, "Failed to retrieve query target options"

    # TODO: what else do we want to do here
    print(f"confluence query target option definitions: {truncate_str(confluence_query_target_options.definitions)}")
    print(f"confluence query target option selectors: {truncate_str(confluence_query_target_options.selectors)}")

    return True