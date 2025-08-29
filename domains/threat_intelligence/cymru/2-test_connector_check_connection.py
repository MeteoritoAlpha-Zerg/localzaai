# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to Team Cymru"""
    print("Testing Team Cymru connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    teamcymru_api_key = zerg_state.get("teamcymru_api_key").get("value")
    teamcymru_api_secret = zerg_state.get("teamcymru_api_secret").get("value")
    teamcymru_username = zerg_state.get("teamcymru_username").get("value")

    from connectors.teamcymru.config import TeamCymruConnectorConfig
    from connectors.teamcymru.connector import TeamCymruConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = TeamCymruConnectorConfig(
        api_key=teamcymru_api_key,
        api_secret=teamcymru_api_secret,
        username=teamcymru_username,
    )
    assert isinstance(config, ConnectorConfig), "TeamCymruConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = TeamCymruConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TeamCymruConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True