# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing Splunk Phantom connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    splunk_phantom_api_url = zerg_state.get("splunk_phantom_api_url").get("value")
    splunk_phantom_api_token = zerg_state.get("splunk_phantom_api_token").get("value")

    from connectors.splunk_phantom.config import SplunkPhantomConnectorConfig
    from connectors.splunk_phantom.connector import SplunkPhantomConnector
    from connectors.splunk_phantom.target import SplunkPhantomTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = SplunkPhantomConnectorConfig(
        api_url=splunk_phantom_api_url,
        api_token=splunk_phantom_api_token,
    )
    assert isinstance(config, ConnectorConfig), "SplunkPhantomConnectorConfig should be of type ConnectorConfig"

    connector = SplunkPhantomConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SplunkPhantomConnector should be of type Connector"

    target = SplunkPhantomTarget()
    assert isinstance(target, ConnectorTargetInterface), "SplunkPhantomTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True