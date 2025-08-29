# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    netography_api_token = zerg_state.get("netography_api_token").get("value")
    netography_base_url = zerg_state.get("netography_base_url").get("value")
    netography_tenant_id = zerg_state.get("netography_tenant_id").get("value")

    from connectors.netography.config import NetographyConnectorConfig
    from connectors.netography.connector import NetographyConnector
    from connectors.netography.target import NetographyTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = NetographyConnectorConfig(
        api_token=netography_api_token,
        base_url=netography_base_url,
        tenant_id=netography_tenant_id,
    )
    assert isinstance(config, ConnectorConfig), "NetographyConnectorConfig should be of type ConnectorConfig"

    connector = NetographyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "NetographyConnector should be of type Connector"

    target = NetographyTarget()
    assert isinstance(target, ConnectorTargetInterface), "NetographyTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True