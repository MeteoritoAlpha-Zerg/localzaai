# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    threatq_api_host = zerg_state.get("threatq_api_host").get("value")
    threatq_api_path = zerg_state.get("threatq_api_path").get("value")
    threatq_username = zerg_state.get("threatq_username").get("value")
    threatq_password = zerg_state.get("threatq_password").get("value")
    threatq_client_id = zerg_state.get("threatq_client_id").get("value")

    from connectors.threatq.config import ThreatQConnectorConfig
    from connectors.threatq.connector import ThreatQConnector
    from connectors.threatq.target import ThreatQTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = ThreatQConnectorConfig(
        api_host=threatq_api_host,
        api_path=threatq_api_path,
        username=threatq_username,
        password=threatq_password,
        client_id=threatq_client_id,
    )
    assert isinstance(config, ConnectorConfig), "ThreatQConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ThreatQConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ThreatQConnector should be of type Connector"

    target = ThreatQTarget()
    assert isinstance(target, ConnectorTargetInterface), "ThreatQTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True