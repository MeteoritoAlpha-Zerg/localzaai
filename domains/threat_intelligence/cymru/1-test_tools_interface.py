# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing Team Cymru connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    teamcymru_api_key = zerg_state.get("teamcymru_api_key").get("value")
    teamcymru_api_secret = zerg_state.get("teamcymru_api_secret").get("value")
    teamcymru_username = zerg_state.get("teamcymru_username").get("value")

    from connectors.teamcymru.config import TeamCymruConnectorConfig
    from connectors.teamcymru.connector import TeamCymruConnector
    from connectors.teamcymru.target import TeamCymruTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = TeamCymruConnectorConfig(
        api_key=teamcymru_api_key,
        api_secret=teamcymru_api_secret,
        username=teamcymru_username,
    )
    assert isinstance(config, ConnectorConfig), "TeamCymruConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = TeamCymruConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TeamCymruConnector should be of type Connector"

    target = TeamCymruTarget()
    assert isinstance(target, ConnectorTargetInterface), "TeamCymruTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True