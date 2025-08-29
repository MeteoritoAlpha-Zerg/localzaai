# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    discord_bot_token = zerg_state.get("discord_bot_token").get("value")
    discord_api_base_url = zerg_state.get("discord_api_base_url").get("value")
    discord_api_version = zerg_state.get("discord_api_version").get("value")

    from connectors.discord.config import DiscordConnectorConfig
    from connectors.discord.connector import DiscordConnector
    from connectors.discord.target import DiscordTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = DiscordConnectorConfig(
        bot_token=discord_bot_token,
        api_base_url=discord_api_base_url,
        api_version=discord_api_version,
    )
    assert isinstance(config, ConnectorConfig), "DiscordConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = DiscordConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DiscordConnector should be of type Connector"

    target = DiscordTarget()
    assert isinstance(target, ConnectorTargetInterface), "DiscordTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True