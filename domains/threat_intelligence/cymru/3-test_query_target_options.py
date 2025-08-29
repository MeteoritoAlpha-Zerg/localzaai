# 3-test_query_target_options.py

async def test_feed_source_enumeration_options(zerg_state=None):
    """Test Team Cymru feed source enumeration by way of query target options"""
    print("Attempting to authenticate using Team Cymru connector")

    assert zerg_state, "this test requires valid zerg_state"

    teamcymru_api_key = zerg_state.get("teamcymru_api_key").get("value")
    teamcymru_api_secret = zerg_state.get("teamcymru_api_secret").get("value")
    teamcymru_username = zerg_state.get("teamcymru_username").get("value")

    from connectors.teamcymru.config import TeamCymruConnectorConfig
    from connectors.teamcymru.connector import TeamCymruConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = TeamCymruConnectorConfig(
        api_key=teamcymru_api_key,
        api_secret=teamcymru_api_secret,
        username=teamcymru_username,
    )
    assert isinstance(config, ConnectorConfig), "TeamCymruConnectorConfig should be of type ConnectorConfig"

    connector = TeamCymruConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TeamCymruConnector should be of type Connector"

    teamcymru_query_target_options = await connector.get_query_target_options()
    assert isinstance(teamcymru_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert teamcymru_query_target_options, "Failed to retrieve query target options"

    print(f"Team Cymru query target option definitions: {teamcymru_query_target_options.definitions}")
    print(f"Team Cymru query target option selectors: {teamcymru_query_target_options.selectors}")

    return True