# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    threatconnect_url = zerg_state.get("threatconnect_url").get("value")
    threatconnect_access_id = zerg_state.get("threatconnect_access_id").get("value")
    threatconnect_secret_key = zerg_state.get("threatconnect_secret_key").get("value")
    threatconnect_default_org = zerg_state.get("threatconnect_default_org").get("value")

    from connectors.threatconnect.config import ThreatConnectConnectorConfig
    from connectors.threatconnect.connector import ThreatConnectConnector
    from connectors.threatconnect.target import ThreatConnectTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = ThreatConnectConnectorConfig(
        url=threatconnect_url,
        access_id=threatconnect_access_id,
        secret_key=threatconnect_secret_key,
        default_org=threatconnect_default_org,
    )
    assert isinstance(config, ConnectorConfig), "ThreatConnectConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ThreatConnectConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ThreatConnectConnector should be of type Connector"

    target = ThreatConnectTarget()
    assert isinstance(target, ConnectorTargetInterface), "ThreatConnectTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True