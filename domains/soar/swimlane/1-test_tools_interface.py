# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    swimlane_host = zerg_state.get("swimlane_host").get("value")
    swimlane_api_token = zerg_state.get("swimlane_api_token").get("value")
    swimlane_user_id = zerg_state.get("swimlane_user_id").get("value")

    from connectors.swimlane_soar.config import SwimlaneSOARConnectorConfig
    from connectors.swimlane_soar.connector import SwimlaneSOARConnector
    from connectors.swimlane_soar.target import SwimlaneSOARTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = SwimlaneSOARConnectorConfig(
        host=swimlane_host,
        api_token=swimlane_api_token,
        user_id=swimlane_user_id,
    )
    assert isinstance(config, ConnectorConfig), "SwimlaneSOARConnectorConfig should be of type ConnectorConfig"

    connector = SwimlaneSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SwimlaneSOARConnector should be of type Connector"

    target = SwimlaneSOARTarget()
    assert isinstance(target, ConnectorTargetInterface), "SwimlaneSOARTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True