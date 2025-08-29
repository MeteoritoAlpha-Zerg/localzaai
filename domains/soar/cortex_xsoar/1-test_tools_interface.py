# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing Cortex XSOAR connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    xsoar_server_url = zerg_state.get("xsoar_server_url").get("value")
    xsoar_api_key = zerg_state.get("xsoar_api_key").get("value")
    xsoar_api_key_id = zerg_state.get("xsoar_api_key_id").get("value")

    from connectors.xsoar.config import XSOARConnectorConfig
    from connectors.xsoar.connector import XSOARConnector
    from connectors.xsoar.target import XSOARTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = XSOARConnectorConfig(
        server_url=xsoar_server_url,
        api_key=xsoar_api_key,
        api_key_id=xsoar_api_key_id,
    )
    assert isinstance(config, ConnectorConfig), "XSOARConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = XSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "XSOARConnector should be of type Connector"

    target = XSOARTarget()
    assert isinstance(target, ConnectorTargetInterface), "XSOARTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True