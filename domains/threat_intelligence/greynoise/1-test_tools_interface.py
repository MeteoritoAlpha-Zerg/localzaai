# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    greynoise_api_key = zerg_state.get("greynoise_api_key").get("value")
    greynoise_base_url = zerg_state.get("greynoise_base_url").get("value")

    from connectors.greynoise.config import GreyNoiseConnectorConfig
    from connectors.greynoise.connector import GreyNoiseConnector
    from connectors.greynoise.target import GreyNoiseTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = GreyNoiseConnectorConfig(
        api_key=greynoise_api_key,
        base_url=greynoise_base_url,
    )
    assert isinstance(config, ConnectorConfig), "GreyNoiseConnectorConfig should be of type ConnectorConfig"

    connector = GreyNoiseConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GreyNoiseConnector should be of type Connector"

    target = GreyNoiseTarget()
    assert isinstance(target, ConnectorTargetInterface), "GreyNoiseTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True