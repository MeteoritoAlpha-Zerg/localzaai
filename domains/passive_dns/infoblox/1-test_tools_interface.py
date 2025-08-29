# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    infoblox_url = zerg_state.get("infoblox_url").get("value")
    infoblox_username = zerg_state.get("infoblox_username").get("value")
    infoblox_password = zerg_state.get("infoblox_password").get("value")
    infoblox_wapi_version = zerg_state.get("infoblox_wapi_version").get("value")

    from connectors.infoblox.config import InfobloxConnectorConfig
    from connectors.infoblox.connector import InfobloxConnector
    from connectors.infoblox.target import InfobloxTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = InfobloxConnectorConfig(
        url=infoblox_url,
        username=infoblox_username,
        password=infoblox_password,
        wapi_version=infoblox_wapi_version,
    )
    assert isinstance(config, ConnectorConfig), "InfobloxConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = InfobloxConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "InfobloxConnector should be of type Connector"

    target = InfobloxTarget()
    assert isinstance(target, ConnectorTargetInterface), "InfobloxTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True