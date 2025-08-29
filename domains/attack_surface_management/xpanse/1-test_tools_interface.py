# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    xpanse_api_url = zerg_state.get("xpanse_api_url").get("value")
    xpanse_api_key = zerg_state.get("xpanse_api_key").get("value")
    xpanse_api_key_id = zerg_state.get("xpanse_api_key_id").get("value")
    xpanse_tenant_id = zerg_state.get("xpanse_tenant_id").get("value")
    xpanse_api_version = zerg_state.get("xpanse_api_version").get("value")

    from connectors.xpanse.config import XpanseConnectorConfig
    from connectors.xpanse.connector import XpanseConnector
    from connectors.xpanse.target import XpanseTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = XpanseConnectorConfig(
        api_url=xpanse_api_url,
        api_key=xpanse_api_key,
        api_key_id=xpanse_api_key_id,
        tenant_id=xpanse_tenant_id,
        api_version=xpanse_api_version,
    )
    assert isinstance(config, ConnectorConfig), "XpanseConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = XpanseConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "XpanseConnector should be of type Connector"

    target = XpanseTarget()
    assert isinstance(target, ConnectorTargetInterface), "XpanseTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True