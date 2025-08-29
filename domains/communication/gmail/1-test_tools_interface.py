# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    gmail_oauth_client_id = zerg_state.get("gmail_oauth_client_id").get("value")
    gmail_oauth_client_secret = zerg_state.get("gmail_oauth_client_secret").get("value")
    gmail_oauth_refresh_token = zerg_state.get("gmail_oauth_refresh_token").get("value")
    gmail_api_base_url = zerg_state.get("gmail_api_base_url").get("value")
    gmail_api_version = zerg_state.get("gmail_api_version").get("value")

    from connectors.gmail.config import GmailConnectorConfig
    from connectors.gmail.connector import GmailConnector
    from connectors.gmail.target import GmailTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = GmailConnectorConfig(
        oauth_client_id=gmail_oauth_client_id,
        oauth_client_secret=gmail_oauth_client_secret,
        oauth_refresh_token=gmail_oauth_refresh_token,
        api_base_url=gmail_api_base_url,
        api_version=gmail_api_version,
    )
    assert isinstance(config, ConnectorConfig), "GmailConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = GmailConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GmailConnector should be of type Connector"

    target = GmailTarget()
    assert isinstance(target, ConnectorTargetInterface), "GmailTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True