# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing MISP connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    misp_url = zerg_state.get("misp_url").get("value")
    misp_api_key = zerg_state.get("misp_api_key").get("value")

    from connectors.misp.config import MISPConnectorConfig
    from connectors.misp.connector import MISPConnector
    from connectors.misp.target import MISPTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = MISPConnectorConfig(
        url=misp_url,
        api_key=misp_api_key,
    )
    assert isinstance(config, ConnectorConfig), "MISPConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = MISPConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MISPConnector should be of type Connector"

    target = MISPTarget()
    assert isinstance(target, ConnectorTargetInterface), "MISPTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True