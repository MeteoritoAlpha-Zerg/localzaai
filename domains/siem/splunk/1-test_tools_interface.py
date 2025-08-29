# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    splunk_host = zerg_state.get("splunk_host").get("value")
    splunk_port = zerg_state.get("splunk_port").get("value")
    splunk_username = zerg_state.get("splunk_username").get("value")
    splunk_password = zerg_state.get("splunk_password").get("value")
    splunk_hec_token = zerg_state.get("splunk_hec_token").get("value")

    from connectors.splunk.config import SplunkConnectorConfig
    from connectors.splunk.connector import SplunkConnector
    from connectors.splunk.target import SplunkTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = SplunkConnectorConfig(
        host=splunk_host,
        port=int(splunk_port),
        username=splunk_username,
        password=splunk_password,
        hec_token=splunk_hec_token,
    )
    assert isinstance(config, ConnectorConfig), "SplunkConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = SplunkConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SplunkConnector should be of type Connector"

    target = SplunkTarget()
    assert isinstance(target, ConnectorTargetInterface), "SplunkTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True