# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    taxii_server_url = zerg_state.get("taxii_server_url").get("value")
    taxii_username = zerg_state.get("taxii_username").get("value")
    taxii_password = zerg_state.get("taxii_password").get("value")

    from connectors.stix_taxii.config import STIXTAXIIConnectorConfig
    from connectors.stix_taxii.connector import STIXTAXIIConnector
    from connectors.stix_taxii.target import STIXTAXIITarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = STIXTAXIIConnectorConfig(
        server_url=taxii_server_url,
        username=taxii_username,
        password=taxii_password,
    )
    assert isinstance(config, ConnectorConfig), "STIXTAXIIConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = STIXTAXIIConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "STIXTAXIIConnector should be of type Connector"

    target = STIXTAXIITarget()
    assert isinstance(target, ConnectorTargetInterface), "STIXTAXIITarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True