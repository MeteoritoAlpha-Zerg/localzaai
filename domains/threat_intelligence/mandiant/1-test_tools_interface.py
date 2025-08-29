# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    mandiant_url = zerg_state.get("mandiant_url").get("value")
    mandiant_api_key = zerg_state.get("mandiant_api_key").get("value")
    mandiant_secret_key = zerg_state.get("mandiant_secret_key").get("value")

    from connectors.mandiant.config import MandiantConnectorConfig
    from connectors.mandiant.connector import MandiantConnector
    from connectors.mandiant.target import MandiantTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = MandiantConnectorConfig(
        url=mandiant_url,
        api_key=mandiant_api_key,
        secret_key=mandiant_secret_key,
    )
    assert isinstance(config, ConnectorConfig), "MandiantConnectorConfig should be of type ConnectorConfig"

    connector = MandiantConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MandiantConnector should be of type Connector"

    target = MandiantTarget()
    assert isinstance(target, ConnectorTargetInterface), "MandiantTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True