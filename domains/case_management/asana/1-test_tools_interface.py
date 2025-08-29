# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    asana_personal_access_token = zerg_state.get("asana_personal_access_token").get("value")

    from connectors.asana.config import AsanaConnectorConfig
    from connectors.asana.connector import AsanaConnector
    from connectors.asana.target import AsanaTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = AsanaConnectorConfig(
        personal_access_token=asana_personal_access_token,
    )
    assert isinstance(config, ConnectorConfig), "AsanaConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = AsanaConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "AsanaConnector should be of type Connector"

    target = AsanaTarget()
    assert isinstance(target, ConnectorTargetInterface), "AsanaTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True