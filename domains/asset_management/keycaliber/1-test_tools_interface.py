# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    keycaliber_host = zerg_state.get("keycaliber_host").get("value")
    keycaliber_api_key = zerg_state.get("keycaliber_api_key").get("value")

    from connectors.keycaliber.config import KeyCaliberConnectorConfig
    from connectors.keycaliber.connector import KeyCaliberConnector
    from connectors.keycaliber.target import KeyCaliberTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = KeyCaliberConnectorConfig(
        host=keycaliber_host,
        api_key=keycaliber_api_key,
    )
    assert isinstance(config, ConnectorConfig), "KeyCaliberConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = KeyCaliberConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "KeyCaliberConnector should be of type Connector"

    target = KeyCaliberTarget()
    assert isinstance(target, ConnectorTargetInterface), "KeyCaliberTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True