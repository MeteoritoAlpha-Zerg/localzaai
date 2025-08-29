# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing CISA connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    cisa_base_url = zerg_state.get("cisa_base_url").get("value")
    cisa_kev_url = zerg_state.get("cisa_kev_url").get("value")

    from connectors.cisa.config import CISAConnectorConfig
    from connectors.cisa.connector import CISAConnector
    from connectors.cisa.target import CISATarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = CISAConnectorConfig(
        base_url=cisa_base_url,
        kev_url=cisa_kev_url,
    )
    assert isinstance(config, ConnectorConfig), "CISAConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = CISAConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CISAConnector should be of type Connector"

    target = CISATarget()
    assert isinstance(target, ConnectorTargetInterface), "CISATarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True