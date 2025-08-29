# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing Rapid7 InsightIDR connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    rapid7_insightidr_api_url = zerg_state.get("rapid7_insightidr_api_url").get("value")
    rapid7_insightidr_api_key = zerg_state.get("rapid7_insightidr_api_key").get("value")

    from connectors.rapid7_insightidr.config import Rapid7InsightIDRConnectorConfig
    from connectors.rapid7_insightidr.connector import Rapid7InsightIDRConnector
    from connectors.rapid7_insightidr.target import Rapid7InsightIDRTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = Rapid7InsightIDRConnectorConfig(
        api_url=rapid7_insightidr_api_url,
        api_key=rapid7_insightidr_api_key,
    )
    assert isinstance(config, ConnectorConfig), "Rapid7InsightIDRConnectorConfig should be of type ConnectorConfig"

    connector = Rapid7InsightIDRConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "Rapid7InsightIDRConnector should be of type Connector"

    target = Rapid7InsightIDRTarget()
    assert isinstance(target, ConnectorTargetInterface), "Rapid7InsightIDRTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True