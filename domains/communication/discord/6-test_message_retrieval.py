# 6-test_message_retrieval.py

async def test_message_retrieval(zerg_state=None):
    """Test Discord message retrieval by way of connector tools"""
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
    assert guild_selector, "failed to retrieve guild selector"

    guild_id = guild_selector.values[0] if guild_selector.values else None
    assert guild_id, "failed to retrieve guild ID"

    # Get channels first to find a text channel
    target = DiscordTarget(guild_ids=[guild_id])
    tools = await connector.get_tools(target=target)
    
    get_channels_tool = next(tool for tool in tools if tool.name == "get_discord_channels")
    channels_result = await get_channels_tool.execute(guild_id=guild_id)
    channels = channels_result.result
    
    # Find a text channel (type 0)
    text_channels = [ch for ch in channels if ch.get("type") == 0]
    assert len(text_channels) > 0, "No text channels found in guild"
    
    channel_id = text_channels[0]["id"]
    print(f"Selecting channel ID: {channel_id}")

    # Execute message retrieval
    get_messages_tool = next(tool for tool in tools if tool.name == "get_discord_messages")
    messages_result = await get_messages_tool.execute(channel_id=channel_id, limit=50)
    discord_messages = messages_result.result

    print("Type of returned discord_messages:", type(discord_messages))
    print(f"len messages: {len(discord_messages)} messages: {str(discord_messages)[:200]}")

    # Validate results
    assert isinstance(discord_messages, list), "discord_messages should be a list"
    # Note: messages list might be empty if channel has no messages, so we don't assert length > 0

    # If we have messages, verify their structure
    if len(discord_messages) > 0:
        messages_to_check = discord_messages[:5] if len(discord_messages) > 5 else discord_messages
        
        for message in messages_to_check:
            assert "id" in message, "Each message should have an 'id' field"
            assert "content" in message, "Each message should have a 'content' field"
            assert "author" in message, "Each message should have an 'author' field"
            assert "timestamp" in message, "Each message should have a 'timestamp' field"
            
            # Verify channel_id matches if present
            if "channel_id" in message:
                assert message["channel_id"] == channel_id, "Message channel_id should match target channel"
            
            # Check for additional message fields
            message_fields = ["embeds", "reactions", "attachments", "mentions"]
            present_fields = [field for field in message_fields if field in message]
            print(f"Message {message['id']} contains: {', '.join(present_fields)}")
            
            # Verify author structure
            author = message["author"]
            assert isinstance(author, dict), "Author should be a dictionary"
            assert "id" in author, "Author should have an 'id' field"
            assert "username" in author, "Author should have a 'username' field"

        print(f"Successfully retrieved and validated {len(discord_messages)} Discord messages")
    else:
        print("Channel contains no messages - validation passed")

    return True