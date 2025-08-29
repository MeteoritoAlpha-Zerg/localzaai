# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    teams_client_id = zerg_state.get("teams_client_id").get("value")
    teams_client_secret = zerg_state.get("teams_client_secret").get("value")
    teams_tenant_id = zerg_state.get("teams_tenant_id").get("value")
    teams_scope = zerg_state.get("teams_scope").get("value")
    teams_api_base_url = zerg_state.get("teams_api_base_url").get("value")

    from connectors.teams.config import TeamsConnectorConfig
    from connectors.teams.connector import TeamsConnector
    from connectors.teams.target import TeamsTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = TeamsConnectorConfig(
        client_id=teams_client_id,
        client_secret=teams_client_secret,
        tenant_id=teams_tenant_id,
        scope=teams_scope,
        api_base_url=teams_api_base_url,
    )
    assert isinstance(config, ConnectorConfig), "TeamsConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = TeamsConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TeamsConnector should be of type Connector"

    target = TeamsTarget()
    assert isinstance(target, ConnectorTargetInterface), "TeamsTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True