# 3-test_query_target_options.py

async def test_board_enumeration_options(zerg_state=None):
    """Test Trello board enumeration by way of query target options"""
    print("Attempting to authenticate using Trello connector")

    assert zerg_state, "this test requires valid zerg_state"

    trello_api_key = zerg_state.get("trello_api_key").get("value")
    trello_api_token = zerg_state.get("trello_api_token").get("value")
    trello_url = zerg_state.get("trello_url").get("value")

    from connectors.trello.config import TrelloConnectorConfig
    from connectors.trello.connector import TrelloConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = TrelloConnectorConfig(
        api_key=trello_api_key,
        api_token=trello_api_token,
        url=trello_url,
    )
    assert isinstance(config, ConnectorConfig), "TrelloConnectorConfig should be of type ConnectorConfig"

    connector = TrelloConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TrelloConnector should be of type Connector"

    trello_query_target_options = await connector.get_query_target_options()
    assert isinstance(trello_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert trello_query_target_options, "Failed to retrieve query target options"

    print(f"trello query target option definitions: {trello_query_target_options.definitions}")
    print(f"trello query target option selectors: {trello_query_target_options.selectors}")

    return True