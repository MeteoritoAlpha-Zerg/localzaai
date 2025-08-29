# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    trello_api_key = zerg_state.get("trello_api_key").get("value")
    trello_api_token = zerg_state.get("trello_api_token").get("value")
    trello_url = zerg_state.get("trello_url").get("value")

    from connectors.trello.config import TrelloConnectorConfig
    from connectors.trello.connector import TrelloConnector
    from connectors.trello.target import TrelloTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
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

    target = TrelloTarget()
    assert isinstance(target, ConnectorTargetInterface), "TrelloTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True