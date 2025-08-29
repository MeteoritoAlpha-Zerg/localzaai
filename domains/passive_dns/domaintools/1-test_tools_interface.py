# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    domaintools_api_username = zerg_state.get("domaintools_api_username").get("value")
    domaintools_api_key = zerg_state.get("domaintools_api_key").get("value")
    domaintools_base_url = zerg_state.get("domaintools_base_url").get("value")

    from connectors.domaintools.config import DomainToolsConnectorConfig
    from connectors.domaintools.connector import DomainToolsConnector
    from connectors.domaintools.target import DomainToolsTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = DomainToolsConnectorConfig(
        api_username=domaintools_api_username,
        api_key=domaintools_api_key,
        base_url=domaintools_base_url,
    )
    assert isinstance(config, ConnectorConfig), "DomainToolsConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = DomainToolsConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DomainToolsConnector should be of type Connector"

    target = DomainToolsTarget()
    assert isinstance(target, ConnectorTargetInterface), "DomainToolsTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True