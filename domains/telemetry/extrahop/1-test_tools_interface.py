# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing ExtraHop connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    extrahop_server_url = zerg_state.get("extrahop_server_url").get("value")
    extrahop_api_key = zerg_state.get("extrahop_api_key").get("value")
    extrahop_api_secret = zerg_state.get("extrahop_api_secret").get("value")

    from connectors.extrahop.config import ExtraHopConnectorConfig
    from connectors.extrahop.connector import ExtraHopConnector
    from connectors.extrahop.target import ExtraHopTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = ExtraHopConnectorConfig(
        server_url=extrahop_server_url,
        api_key=extrahop_api_key,
        api_secret=extrahop_api_secret,
    )
    assert isinstance(config, ConnectorConfig), "ExtraHopConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ExtraHopConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ExtraHopConnector should be of type Connector"

    target = ExtraHopTarget()
    assert isinstance(target, ConnectorTargetInterface), "ExtraHopTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True