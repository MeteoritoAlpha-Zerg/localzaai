# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing Cisco Stealthwatch connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    cisco_stealthwatch_api_url = zerg_state.get("cisco_stealthwatch_api_url").get("value")
    cisco_stealthwatch_username = zerg_state.get("cisco_stealthwatch_username").get("value")
    cisco_stealthwatch_password = zerg_state.get("cisco_stealthwatch_password").get("value")

    from connectors.cisco_stealthwatch.config import CiscoStealthwatchConnectorConfig
    from connectors.cisco_stealthwatch.connector import CiscoStealthwatchConnector
    from connectors.cisco_stealthwatch.target import CiscoStealthwatchTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = CiscoStealthwatchConnectorConfig(
        api_url=cisco_stealthwatch_api_url,
        username=cisco_stealthwatch_username,
        password=cisco_stealthwatch_password,
    )
    assert isinstance(config, ConnectorConfig), "CiscoStealthwatchConnectorConfig should be of type ConnectorConfig"

    connector = CiscoStealthwatchConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CiscoStealthwatchConnector should be of type Connector"

    target = CiscoStealthwatchTarget()
    assert isinstance(target, ConnectorTargetInterface), "CiscoStealthwatchTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True