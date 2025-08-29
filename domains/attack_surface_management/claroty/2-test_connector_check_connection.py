# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing claroty connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    claroty_server_url = zerg_state.get("claroty_server_url").get("value")
    claroty_api_token = zerg_state.get("claroty_api_token").get("value")
    claroty_username = zerg_state.get("claroty_username").get("value")
    claroty_password = zerg_state.get("claroty_password").get("value")
    claroty_api_version = zerg_state.get("claroty_api_version").get("value")

    from connectors.claroty.config import ClarotyConnectorConfig
    from connectors.claroty.connector import ClarotyConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = ClarotyConnectorConfig(
        server_url=claroty_server_url,
        api_token=claroty_api_token,
        username=claroty_username,
        password=claroty_password,
        api_version=claroty_api_version,
    )
    assert isinstance(config, ConnectorConfig), "ClarotyConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ClarotyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ClarotyConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True