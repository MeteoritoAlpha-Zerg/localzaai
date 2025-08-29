# 5-test_channel_retrieval.py

async def test_channel_retrieval(zerg_state=None):
    """Test Discord channel retrieval by way of connector tools"""
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

    connector = DiscordConnector
    await connector.initialize(config=config, user_id="test_user_id", encryption_key="test_enc_key")

    # Get query target options and select guild
    discord_query_target_options = await connector.get_query_target_options()
    guild_selector = next((s for s in discord_query_target_options.selectors if s.type == 'guild_ids'), None)
    assert guild_selector, "failed to retrieve guild selector from query target options"

    assert isinstance(guild_selector.values, list), "guild_selector values must be a list"
    guild_id = guild_selector.values[0] if guild_selector.values else None
    print(f"Selecting guild ID: {guild_id}")
    assert guild_id, "failed to retrieve guild ID from guild selector"

    # Set up target and get tools
    target = DiscordTarget(guild_ids=[guild_id])
    tools = await connector.get_tools(target=target)

    # Execute channel retrieval
    get_discord_channels_tool = next(tool for tool in tools if tool.name == "get_discord_channels")
    discord_channels_result = await get_discord_channels_tool.execute(guild_id=guild_id)
    discord_channels = discord_channels_result.result

    print("Type of returned discord_channels:", type(discord_channels))
    print(f"len channels: {len(discord_channels)} channels: {str(discord_channels)[:200]}")

    # Validate results
    assert isinstance(discord_channels, list), "discord_channels should be a list"
    assert len(discord_channels) > 0, "discord_channels should not be empty"

    # Verify structure of each channel object
    channels_to_check = discord_channels[:5] if len(discord_channels) > 5 else discord_channels
    
    for channel in channels_to_check:
        assert "id" in channel, "Each channel should have an 'id' field"
        assert "name" in channel, "Each channel should have a 'name' field"
        assert "type" in channel, "Each channel should have a 'type' field"
        
        # Verify channel type is valid Discord channel type
        valid_types = [0, 1, 2, 4, 5, 10, 11, 12, 13, 15]  # Discord channel types
        assert channel["type"] in valid_types, f"Channel type {channel['type']} should be valid Discord type"
        
        # Check for additional channel fields
        channel_fields = ["guild_id", "position", "permission_overwrites", "topic"]
        present_fields = [field for field in channel_fields if field in channel]
        print(f"Channel {channel['name']} contains: {', '.join(present_fields)}")
        
        # Verify guild_id matches if present
        if "guild_id" in channel:
            assert channel["guild_id"] == guild_id, f"Channel guild_id should match target guild"

    print(f"Successfully retrieved and validated {len(discord_channels)} Discord channels")
    return True