# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    proofpoint_api_host = zerg_state.get("proofpoint_api_host").get("value")
    proofpoint_principal = zerg_state.get("proofpoint_principal").get("value")
    proofpoint_secret = zerg_state.get("proofpoint_secret").get("value")

    from connectors.proofpoint.config import ProofpointConnectorConfig
    from connectors.proofpoint.connector import ProofpointConnector
    from connectors.proofpoint.target import ProofpointTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = ProofpointConnectorConfig(
        api_host=proofpoint_api_host,
        principal=proofpoint_principal,
        secret=proofpoint_secret,
    )
    assert isinstance(config, ConnectorConfig), "ProofpointConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ProofpointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ProofpointConnector should be of type Connector"

    target = ProofpointTarget()
    assert isinstance(target, ConnectorTargetInterface), "ProofpointTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True