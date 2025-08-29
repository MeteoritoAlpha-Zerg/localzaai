# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    github_api_url = zerg_state.get("github_api_url").get("value")
    github_access_token = zerg_state.get("github_access_token").get("value")

    from connectors.github.config import GithubConnectorConfig
    from connectors.github.connector import GithubConnector
    from connectors.github.target import GithubTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

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

    target = GithubTarget()
    assert isinstance(target, ConnectorTargetInterface), "GithubTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True