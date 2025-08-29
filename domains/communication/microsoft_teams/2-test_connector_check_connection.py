# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing teams connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    teams_client_id = zerg_state.get("teams_client_id").get("value")
    teams_client_secret = zerg_state.get("teams_client_secret").get("value")
    teams_tenant_id = zerg_state.get("teams_tenant_id").get("value")
    teams_scope = zerg_state.get("teams_scope").get("value")
    teams_api_base_url = zerg_state.get("teams_api_base_url").get("value")

    from connectors.teams.config import TeamsConnectorConfig
    from connectors.teams.connector import TeamsConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = TeamsConnectorConfig(
        client_id=teams_client_id,
        client_secret=teams_client_secret,
        tenant_id=teams_tenant_id,
        scope=teams_scope,
        api_base_url=teams_api_base_url,
    )
    assert isinstance(config, ConnectorConfig), "TeamsConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = TeamsConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TeamsConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True