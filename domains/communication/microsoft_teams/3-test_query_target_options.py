# 3-test_query_target_options.py

async def test_team_enumeration_options(zerg_state=None):
    """Test Microsoft Teams enumeration by way of query target options"""
    print("Attempting to authenticate using Teams connector")

    assert zerg_state, "this test requires valid zerg_state"

    teams_client_id = zerg_state.get("teams_client_id").get("value")
    teams_client_secret = zerg_state.get("teams_client_secret").get("value")
    teams_tenant_id = zerg_state.get("teams_tenant_id").get("value")
    teams_scope = zerg_state.get("teams_scope").get("value")
    teams_api_base_url = zerg_state.get("teams_api_base_url").get("value")

    from connectors.teams.config import TeamsConnectorConfig
    from connectors.teams.connector import TeamsConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = TeamsConnectorConfig(
        client_id=teams_client_id,
        client_secret=teams_client_secret,
        tenant_id=teams_tenant_id,
        scope=teams_scope,
        api_base_url=teams_api_base_url,
    )
    assert isinstance(config, ConnectorConfig), "TeamsConnectorConfig should be of type ConnectorConfig"

    connector = TeamsConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TeamsConnector should be of type Connector"

    teams_query_target_options = await connector.get_query_target_options()
    assert isinstance(teams_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert teams_query_target_options, "Failed to retrieve query target options"

    print(f"teams query target option definitions: {teams_query_target_options.definitions}")
    print(f"teams query target option selectors: {teams_query_target_options.selectors}")

    return True