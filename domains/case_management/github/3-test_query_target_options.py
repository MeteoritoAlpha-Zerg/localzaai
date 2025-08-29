# 3-test_query_target_options.py

async def test_project_enumeration_options(zerg_state=None):
    """Test Github project enumeration by way of query target options"""
    print("Attempting to authenticate using Github connector")

    assert zerg_state, "this test requires valid zerg_state"

    github_api_url = zerg_state.get("github_api_url").get("value")
    github_access_token = zerg_state.get("github_access_token").get("value")

    from connectors.github.config import GithubConnectorConfig
    from connectors.github.connector import GithubConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = GithubConnectorConfig(
        url=github_api_url,
        access_token=github_access_token,
    )
    assert isinstance(config, ConnectorConfig), "GithubConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = GithubConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GithubConnector should be of type Connector"

    query_target_options = await connector.get_query_target_options()
    assert isinstance(query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert query_target_options, "Failed to retrieve query target options"

    print(f"jira query target option definitions: {query_target_options.definitions}")
    print(f"jira query target option selectors: {query_target_options.selectors}")

    return True