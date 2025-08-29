# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing ArcSight connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    arcsight_server_url = zerg_state.get("arcsight_server_url").get("value")
    arcsight_username = zerg_state.get("arcsight_username").get("value")
    arcsight_password = zerg_state.get("arcsight_password").get("value")

    from connectors.arcsight.config import ArcSightConnectorConfig
    from connectors.arcsight.connector import ArcSightConnector
    from connectors.arcsight.target import ArcSightTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = ArcSightConnectorConfig(
        server_url=arcsight_server_url,
        username=arcsight_username,
        password=arcsight_password,
    )
    assert isinstance(config, ConnectorConfig), "ArcSightConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ArcSightConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ArcSightConnector should be of type Connector"

    target = ArcSightTarget()
    assert isinstance(target, ConnectorTargetInterface), "ArcSightTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True