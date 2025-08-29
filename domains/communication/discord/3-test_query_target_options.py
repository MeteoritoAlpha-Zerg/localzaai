# 3-test_query_target_options.py

async def test_guild_enumeration_options(zerg_state=None):
    """Test Discord guild enumeration by way of query target options"""
    print("Attempting to authenticate using Discord connector")

    assert zerg_state, "this test requires valid zerg_state"

    discord_bot_token = zerg_state.get("discord_bot_token").get("value")
    discord_api_base_url = zerg_state.get("discord_api_base_url").get("value")
    discord_api_version = zerg_state.get("discord_api_version").get("value")

    from connectors.discord.config import DiscordConnectorConfig
    from connectors.discord.connector import DiscordConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = DiscordConnectorConfig(
        bot_token=discord_bot_token,
        api_base_url=discord_api_base_url,
        api_version=discord_api_version,
    )
    assert isinstance(config, ConnectorConfig), "DiscordConnectorConfig should be of type ConnectorConfig"

    connector = DiscordConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DiscordConnector should be of type Connector"

    discord_query_target_options = await connector.get_query_target_options()
    assert isinstance(discord_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert discord_query_target_options, "Failed to retrieve query target options"

    print(f"discord query target option definitions: {discord_query_target_options.definitions}")
    print(f"discord query target option selectors: {discord_query_target_options.selectors}")

    return True