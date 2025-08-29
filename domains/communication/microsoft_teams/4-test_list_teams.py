# 4-test_list_teams.py

async def test_list_teams(zerg_state=None):
    """Test Microsoft Teams enumeration by way of connector tools"""
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

    # Get query target options and select teams
    teams_query_target_options = await connector.get_query_target_options()
    team_selector = next((s for s in teams_query_target_options.selectors if s.type == 'team_ids'), None)
    assert team_selector, "failed to retrieve team selector from query target options"

    num_teams = 2
    team_ids = team_selector.values[:num_teams] if team_selector.values else None
    print(f"Selecting team IDs: {team_ids}")
    assert team_ids, f"failed to retrieve {num_teams} team IDs from team selector"

    # Set up target and get tools
    target = TeamsTarget(team_ids=team_ids)
    assert isinstance(target, ConnectorTargetInterface), "TeamsTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    get_teams_tool = next(tool for tool in tools if tool.name == "get_teams_info")
    teams_result = await get_teams_tool.execute()
    ms_teams = teams_result.result

    print("Type of returned ms_teams:", type(ms_teams))
    print(f"len teams: {len(ms_teams)} teams: {str(ms_teams)[:200]}")

    # Validate results
    assert isinstance(ms_teams, list), "ms_teams should be a list"
    assert len(ms_teams) > 0, "ms_teams should not be empty"

    # Verify structure of each team object
    for team in ms_teams:
        assert "id" in team, "Each team should have an 'id' field"
        assert team["id"] in team_ids, f"Team ID {team['id']} is not in the requested team_ids"
        assert "displayName" in team, "Each team should have a 'displayName' field"
        
        # Check for additional team fields
        team_fields = ["description", "webUrl", "createdDateTime", "memberSettings"]
        present_fields = [field for field in team_fields if field in team]
        print(f"Team {team['displayName']} contains: {', '.join(present_fields)}")

    print(f"Successfully retrieved and validated {len(ms_teams)} Microsoft Teams")
    return True