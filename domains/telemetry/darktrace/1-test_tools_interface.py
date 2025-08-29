# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    darktrace_url = zerg_state.get("darktrace_url").get("value")
    darktrace_public_token = zerg_state.get("darktrace_public_token").get("value")
    darktrace_private_token = zerg_state.get("darktrace_private_token").get("value")

    from connectors.darktrace.config import DarktraceConnectorConfig
    from connectors.darktrace.connector import DarktraceConnector
    from connectors.darktrace.target import DarktraceTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = DarktraceConnectorConfig(
        url=darktrace_url,
        public_token=darktrace_public_token,
        private_token=darktrace_private_token,
    )
    assert isinstance(config, ConnectorConfig), "DarktraceConnectorConfig should be of type ConnectorConfig"

    connector = DarktraceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DarktraceConnector should be of type Connector"

    target = DarktraceTarget()
    assert isinstance(target, ConnectorTargetInterface), "DarktraceTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True