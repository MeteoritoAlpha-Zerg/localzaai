# 4-test_list_guilds.py

async def test_list_guilds(zerg_state=None):
    """Test Discord guild enumeration by way of query target options"""
    print("Attempting to authenticate using Discord connector")

    assert zerg_state, "this test requires valid zerg_state"

    # Config setup
    discord_bot_token = zerg_state.get("discord_bot_token").get("value")
    discord_api_base_url = zerg_state.get("discord_api_base_url").get("value")
    discord_api_version = zerg_state.get("discord_api_version").get("value")

    from connectors.discord.config import DiscordConnectorConfig
    from connectors.discord.connector import DiscordConnector
    from connectors.discord.target import DiscordTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = DiscordConnectorConfig(
        bot_token=discord_bot_token, api_base_url=discord_api_base_url, api_version=discord_api_version
    )
    assert isinstance(config, ConnectorConfig), "DiscordConnectorConfig should be of type ConnectorConfig"

    connector = DiscordConnector
    await connector.initialize(config=config, user_id="test_user_id", encryption_key="test_enc_key")
    assert isinstance(connector, Connector), "DiscordConnector should be of type Connector"

    # Get query target options and select guilds
    discord_query_target_options = await connector.get_query_target_options()
    guild_selector = next((s for s in discord_query_target_options.selectors if s.type == 'guild_ids'), None)
    assert guild_selector, "failed to retrieve guild selector from query target options"

    num_guilds = 2
    assert isinstance(guild_selector.values, list), "guild_selector values must be a list"
    guild_ids = guild_selector.values[:num_guilds] if guild_selector.values else None
    print(f"Selecting guild IDs: {guild_ids}")
    assert guild_ids, f"failed to retrieve {num_guilds} guild IDs from guild selector"

    # Set up target and get tools
    target = DiscordTarget(guild_ids=guild_ids)
    assert isinstance(target, ConnectorTargetInterface), "DiscordTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Execute guild retrieval
    discord_get_guilds_tool = next(tool for tool in tools if tool.name == "get_discord_guilds")
    discord_guilds_result = await discord_get_guilds_tool.execute()
    discord_guilds = discord_guilds_result.result

    print("Type of returned discord_guilds:", type(discord_guilds))
    print(f"len guilds: {len(discord_guilds)} guilds: {str(discord_guilds)[:200]}")

    # Validate results
    assert isinstance(discord_guilds, list), "discord_guilds should be a list"
    assert len(discord_guilds) > 0, "discord_guilds should not be empty"
    assert len(discord_guilds) == num_guilds, f"discord_guilds should have {num_guilds} entries"

    # Verify structure of each guild object
    for guild in discord_guilds:
        assert "id" in guild, "Each guild should have an 'id' field"
        assert guild["id"] in guild_ids, f"Guild ID {guild['id']} is not in the requested guild_ids"
        
        # Verify essential Discord guild fields
        assert "name" in guild, "Each guild should have a 'name' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["description", "icon", "owner_id", "member_count"]
        present_fields = [field for field in descriptive_fields if field in guild]
        print(f"Guild {guild['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first guild
        if guild == discord_guilds[0]:
            print(f"Example guild structure: {guild}")

    print(f"Successfully retrieved and validated {len(discord_guilds)} Discord guilds")
    return True