# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing Recorded Future connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    rf_api_url = zerg_state.get("recorded_future_api_url").get("value")
    rf_api_token = zerg_state.get("recorded_future_api_token").get("value")

    from connectors.recorded_future.config import RecordedFutureConnectorConfig
    from connectors.recorded_future.connector import RecordedFutureConnector
    from connectors.recorded_future.target import RecordedFutureTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = RecordedFutureConnectorConfig(
        api_url=rf_api_url,
        api_token=rf_api_token,
    )
    assert isinstance(config, ConnectorConfig), "RecordedFutureConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = RecordedFutureConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RecordedFutureConnector should be of type Connector"

    target = RecordedFutureTarget()
    assert isinstance(target, ConnectorTargetInterface), "RecordedFutureTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True