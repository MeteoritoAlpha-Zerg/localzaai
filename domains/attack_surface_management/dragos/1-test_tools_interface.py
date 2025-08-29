# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    dragos_api_url = zerg_state.get("dragos_api_url").get("value")
    dragos_api_key = zerg_state.get("dragos_api_key").get("value")
    dragos_api_secret = zerg_state.get("dragos_api_secret").get("value")
    dragos_client_id = zerg_state.get("dragos_client_id").get("value")
    dragos_api_version = zerg_state.get("dragos_api_version").get("value")

    from connectors.dragos.config import DragosConnectorConfig
    from connectors.dragos.connector import DragosConnector
    from connectors.dragos.target import DragosTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = DragosConnectorConfig(
        api_url=dragos_api_url,
        api_key=dragos_api_key,
        api_secret=dragos_api_secret,
        client_id=dragos_client_id,
        api_version=dragos_api_version,
    )
    assert isinstance(config, ConnectorConfig), "DragosConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = DragosConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DragosConnector should be of type Connector"

    target = DragosTarget()
    assert isinstance(target, ConnectorTargetInterface), "DragosTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True