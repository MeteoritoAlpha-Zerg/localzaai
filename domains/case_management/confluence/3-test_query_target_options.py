# 3-test_query_target_options.py

async def test_project_enumeration_options(zerg_state=None):
    """Test Confluence project enumeration by way of query target options"""

    print("Attempting to authenticate using Confluence connector")

    assert zerg_state, "this test requires valid zerg_state"

    confluence_url = zerg_state.get("confluence_url").get("value")
    confluence_api_token = zerg_state.get("confluence_api_token").get("value")
    confluence_email = zerg_state.get("confluence_email").get("value")

    from connectors.confluence.config import ConfluenceConnectorConfig
    from connectors.confluence.connector import ConfluenceConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = ConfluenceConnectorConfig(
        url=confluence_url,
        api_token=confluence_api_token,
        email=confluence_email,
    )
    assert isinstance(config, ConnectorConfig), "ConfluenceConnectorConfig should be of type ConnectorConfig"

    connector = ConfluenceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ConfluenceConnectorConfig should be of type ConnectorConfig"

    confluence_query_target_options = await connector.get_query_target_options()
    assert isinstance(confluence_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert confluence_query_target_options, "Failed to retrieve query target options"

    print(f"confluence query target option definitions: {confluence_query_target_options.definitions}")
    print(f"confluence query target option selectors: {confluence_query_target_options.selectors}")

    return True