# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing OpenDNS (Cisco Umbrella) connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    opendns_api_key = zerg_state.get("opendns_api_key").get("value")
    opendns_api_secret = zerg_state.get("opendns_api_secret").get("value")
    opendns_organization_id = zerg_state.get("opendns_organization_id").get("value")

    from connectors.opendns.config import OpenDNSConnectorConfig
    from connectors.opendns.connector import OpenDNSConnector
    from connectors.opendns.target import OpenDNSTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = OpenDNSConnectorConfig(
        api_key=opendns_api_key,
        api_secret=opendns_api_secret,
        organization_id=opendns_organization_id,
    )
    assert isinstance(config, ConnectorConfig), "OpenDNSConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = OpenDNSConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "OpenDNSConnector should be of type Connector"

    target = OpenDNSTarget()
    assert isinstance(target, ConnectorTargetInterface), "OpenDNSTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True