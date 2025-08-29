# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing trello connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    trello_api_key = zerg_state.get("trello_api_key").get("value")
    trello_api_token = zerg_state.get("trello_api_token").get("value")
    trello_url = zerg_state.get("trello_url").get("value")

    from connectors.trello.config import TrelloConnectorConfig
    from connectors.trello.connector import TrelloConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = TrelloConnectorConfig(
        api_key=trello_api_key,
        api_token=trello_api_token,
        url=trello_url,
    )
    assert isinstance(config, ConnectorConfig), "TrelloConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = TrelloConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TrelloConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True