# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing Flashpoint connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    flashpoint_api_url = zerg_state.get("flashpoint_api_url").get("value")
    flashpoint_api_key = zerg_state.get("flashpoint_api_key").get("value")

    from connectors.flashpoint.config import FlashpointConnectorConfig
    from connectors.flashpoint.connector import FlashpointConnector
    from connectors.flashpoint.target import FlashpointTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = FlashpointConnectorConfig(
        api_url=flashpoint_api_url,
        api_key=flashpoint_api_key,
    )
    assert isinstance(config, ConnectorConfig), "FlashpointConnectorConfig should be of type ConnectorConfig"

    connector = FlashpointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "FlashpointConnector should be of type Connector"

    target = FlashpointTarget()
    assert isinstance(target, ConnectorTargetInterface), "FlashpointTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True