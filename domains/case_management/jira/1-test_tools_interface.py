# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    jira_url = zerg_state.get("jira_url").get("value")
    jira_api_token = zerg_state.get("jira_api_token").get("value")
    jira_email = zerg_state.get("jira_email").get("value")

    from connectors.jira.config import JIRAConnectorConfig
    from connectors.jira.connector import JIRAConnector
    from connectors.jira.target import JIRATarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = JIRAConnectorConfig(
        url=jira_url,
        api_token=jira_api_token,
        email=jira_email,
    )
    assert isinstance(config, ConnectorConfig), "JIRAConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = JIRAConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "JIRAConnector should be of type Connector"

    target = JIRATarget()
    assert isinstance(target, ConnectorTargetInterface), "JIRATarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True