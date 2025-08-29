# 5-test_channel_retrieval.py

async def test_channel_retrieval(zerg_state=None):
    """Test Microsoft Teams channel retrieval by way of connector tools"""
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

    # Get query target options and select team
    teams_query_target_options = await connector.get_query_target_options()
    team_selector = next((s for s in teams_query_target_options.selectors if s.type == 'team_ids'), None)
    assert team_selector, "failed to retrieve team selector"

    team_id = team_selector.values[0] if team_selector.values else None
    print(f"Selecting team ID: {team_id}")
    assert team_id, "failed to retrieve team ID from team selector"

    # Set up target and get tools
    target = TeamsTarget(team_ids=[team_id])
    tools = await connector.get_tools(target=target)

    # Execute channel retrieval
    get_channels_tool = next(tool for tool in tools if tool.name == "get_teams_channels")
    channels_result = await get_channels_tool.execute(team_id=team_id)
    teams_channels = channels_result.result

    print("Type of returned teams_channels:", type(teams_channels))
    print(f"len channels: {len(teams_channels)} channels: {str(teams_channels)[:200]}")

    # Validate results
    assert isinstance(teams_channels, list), "teams_channels should be a list"
    assert len(teams_channels) > 0, "teams_channels should not be empty"

    # Verify structure of each channel object
    channels_to_check = teams_channels[:5] if len(teams_channels) > 5 else teams_channels
    
    for channel in channels_to_check:
        assert "id" in channel, "Each channel should have an 'id' field"
        assert "displayName" in channel, "Each channel should have a 'displayName' field"
        assert "membershipType" in channel, "Each channel should have a 'membershipType' field"
        
        # Verify membership type is valid Teams channel type
        valid_types = ["standard", "private", "unknownFutureValue", "shared"]
        assert channel["membershipType"] in valid_types, f"Channel type {channel['membershipType']} should be valid"
        
        # Check for additional channel fields
        channel_fields = ["description", "webUrl", "createdDateTime", "email"]
        present_fields = [field for field in channel_fields if field in channel]
        print(f"Channel {channel['displayName']} contains: {', '.join(present_fields)}")

    print(f"Successfully retrieved and validated {len(teams_channels)} Teams channels")
    return True