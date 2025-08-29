# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing SecurityScorecard connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    securityscorecard_api_url = zerg_state.get("securityscorecard_api_url").get("value")
    securityscorecard_api_token = zerg_state.get("securityscorecard_api_token").get("value")

    from connectors.securityscorecard.config import SecurityScorecardConnectorConfig
    from connectors.securityscorecard.connector import SecurityScorecardConnector
    from connectors.securityscorecard.target import SecurityScorecardTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = SecurityScorecardConnectorConfig(
        api_url=securityscorecard_api_url,
        api_token=securityscorecard_api_token,
    )
    assert isinstance(config, ConnectorConfig), "SecurityScorecardConnectorConfig should be of type ConnectorConfig"

    connector = SecurityScorecardConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SecurityScorecardConnector should be of type Connector"

    target = SecurityScorecardTarget()
    assert isinstance(target, ConnectorTargetInterface), "SecurityScorecardTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True