# 6-test_message_operations.py

async def test_message_operations(zerg_state=None):
    """Test Microsoft Teams message retrieval and sending by way of connector tools"""
    print("Attempting to authenticate using Teams connector")

    assert zerg_state, "this test requires valid zerg_state"

    # Config setup
    teams_client_id = zerg_state.get("teams_client_id").get("value")
    teams_client_secret = zerg_state.get("teams_client_secret").get("value")
    teams_tenant_id = zerg_state.get("teams_tenant_id").get("value")
    teams_scope = zerg_state.get("teams_scope").get("value")
    teams_api_base_url = zerg_state.get("teams_api_base_url").get("value")

    from connectors.teams.config import TeamsConnectorConfig
    from connectors.teams.connector import TeamsConnector
    from connectors.teams.target import TeamsTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = TeamsConnectorConfig(
        client_id=teams_client_id, client_secret=teams_client_secret, tenant_id=teams_tenant_id,
        scope=teams_scope, api_base_url=teams_api_base_url
    )

    connector = TeamsConnector
    await connector.initialize(config=config, user_id="test_user_id", encryption_key="test_enc_key")

    # Get team and find a standard channel
    teams_query_target_options = await connector.get_query_target_options()
    team_selector = next((s for s in teams_query_target_options.selectors if s.type == 'team_ids'), None)
    team_id = team_selector.values[0] if team_selector.values else None
    assert team_id, "failed to retrieve team ID"

    target = TeamsTarget(team_ids=[team_id])
    tools = await connector.get_tools(target=target)
    
    # Get channels to find a standard channel
    get_channels_tool = next(tool for tool in tools if tool.name == "get_teams_channels")
    channels_result = await get_channels_tool.execute(team_id=team_id)
    channels = channels_result.result
    
    # Find a standard channel for testing
    standard_channels = [ch for ch in channels if ch.get("membershipType") == "standard"]
    assert len(standard_channels) > 0, "No standard channels found in team"
    
    channel_id = standard_channels[0]["id"]
    channel_name = standard_channels[0]["displayName"]
    print(f"Using channel: {channel_name} ({channel_id})")

    # Test message retrieval
    get_messages_tool = next(tool for tool in tools if tool.name == "get_teams_messages")
    messages_result = await get_messages_tool.execute(team_id=team_id, channel_id=channel_id, limit=20)
    teams_messages = messages_result.result

    print("Type of returned teams_messages:", type(teams_messages))
    print(f"len messages: {len(teams_messages)} messages")

    # Validate message retrieval results
    assert isinstance(teams_messages, list), "teams_messages should be a list"
    
    # If we have messages, validate their structure
    if len(teams_messages) > 0:
        for message in teams_messages[:3]:  # Check first 3 messages
            assert "id" in message, "Each message should have an 'id' field"
            assert "createdDateTime" in message, "Each message should have a 'createdDateTime' field"
            
            # Check for message body
            if "body" in message:
                body = message["body"]
                assert isinstance(body, dict), "Message body should be a dictionary"
                assert "content" in body, "Message body should have content"
            
            # Check for sender info
            if "from" in message:
                sender = message["from"]
                assert isinstance(sender, dict), "Sender should be a dictionary"
                print(f"Message from: {sender.get('user', {}).get('displayName', 'Unknown')}")

    # Test message sending
    send_message_tool = next(tool for tool in tools if tool.name == "send_teams_message")
    
    import time
    timestamp = int(time.time())
    test_message = f"Test message from Teams connector - {timestamp}"
    
    send_result = await send_message_tool.execute(
        team_id=team_id,
        channel_id=channel_id,
        content=test_message,
        content_type="text"
    )
    send_response = send_result.result

    print("Type of returned send_response:", type(send_response))
    print(f"Message send response: {str(send_response)[:200]}")

    # Validate send response
    assert isinstance(send_response, dict), "send_response should be a dictionary"
    assert "id" in send_response, "Send response should have an 'id' field"
    
    message_id = send_response["id"]
    print(f"Successfully sent message with ID: {message_id}")

    print("Successfully validated Teams message operations")
    return True