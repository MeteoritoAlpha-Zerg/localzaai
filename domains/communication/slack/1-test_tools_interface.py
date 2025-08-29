# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    slack_bot_token = zerg_state.get("slack_bot_token").get("value")
    slack_workspace_url = zerg_state.get("slack_workspace_url").get("value")

    from connectors.slack.config import SlackConnectorConfig
    from connectors.slack.connector import SlackConnector
    from connectors.slack.target import SlackTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = SlackConnectorConfig(
        bot_token=slack_bot_token,
        workspace_url=slack_workspace_url,
    )
    assert isinstance(config, ConnectorConfig), "SlackConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = SlackConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SlackConnector should be of type Connector"

    target = SlackTarget()
    assert isinstance(target, ConnectorTargetInterface), "SlackTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True