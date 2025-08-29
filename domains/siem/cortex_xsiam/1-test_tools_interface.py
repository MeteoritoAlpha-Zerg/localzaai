# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing Cortex XSIAM connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    cortex_xsiam_api_url = zerg_state.get("cortex_xsiam_api_url").get("value")
    cortex_xsiam_api_key = zerg_state.get("cortex_xsiam_api_key").get("value")
    cortex_xsiam_api_key_id = zerg_state.get("cortex_xsiam_api_key_id").get("value")
    cortex_xsiam_tenant_id = zerg_state.get("cortex_xsiam_tenant_id").get("value")

    from connectors.cortex_xsiam.config import CortexXSIAMConnectorConfig
    from connectors.cortex_xsiam.connector import CortexXSIAMConnector
    from connectors.cortex_xsiam.target import CortexXSIAMTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = CortexXSIAMConnectorConfig(
        api_url=cortex_xsiam_api_url,
        api_key=cortex_xsiam_api_key,
        api_key_id=cortex_xsiam_api_key_id,
        tenant_id=cortex_xsiam_tenant_id,
    )
    assert isinstance(config, ConnectorConfig), "CortexXSIAMConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = CortexXSIAMConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CortexXSIAMConnector should be of type Connector"

    target = CortexXSIAMTarget()
    assert isinstance(target, ConnectorTargetInterface), "CortexXSIAMTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True