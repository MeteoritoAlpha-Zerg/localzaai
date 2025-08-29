# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    humio_api_token = zerg_state.get("humio_api_token").get("value")
    humio_base_url = zerg_state.get("humio_base_url").get("value")
    humio_organization = zerg_state.get("humio_organization").get("value")

    from connectors.crowdstrike_humio.config import CrowdStrikeHumioConnectorConfig
    from connectors.crowdstrike_humio.connector import CrowdStrikeHumioConnector
    from connectors.crowdstrike_humio.target import CrowdStrikeHumioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = CrowdStrikeHumioConnectorConfig(
        api_token=humio_api_token,
        base_url=humio_base_url,
        organization=humio_organization,
    )
    assert isinstance(config, ConnectorConfig), "CrowdStrikeHumioConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = CrowdStrikeHumioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CrowdStrikeHumioConnector should be of type Connector"

    target = CrowdStrikeHumioTarget()
    assert isinstance(target, ConnectorTargetInterface), "CrowdStrikeHumioTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True