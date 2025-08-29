# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    devo_url = zerg_state.get("devo_url").get("value")
    devo_api_key = zerg_state.get("devo_api_key", {}).get("value")
    devo_api_secret = zerg_state.get("devo_api_secret", {}).get("value")
    devo_oauth_token = zerg_state.get("devo_oauth_token", {}).get("value")
    devo_domain = zerg_state.get("devo_domain").get("value")

    from connectors.devo.config import DevoConnectorConfig
    from connectors.devo.connector import DevoConnector
    from connectors.devo.target import DevoTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config - prefer OAuth token over API key/secret
    if devo_oauth_token:
        config = DevoConnectorConfig(
            url=devo_url,
            oauth_token=devo_oauth_token,
            default_domain=devo_domain,
        )
    elif devo_api_key and devo_api_secret:
        config = DevoConnectorConfig(
            url=devo_url,
            api_key=devo_api_key,
            api_secret=devo_api_secret,
            default_domain=devo_domain,
        )
    else:
        raise Exception("Either devo_oauth_token or both devo_api_key and devo_api_secret must be provided")

    assert isinstance(config, ConnectorConfig), "DevoConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = DevoConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DevoConnector should be of type Connector"

    target = DevoTarget()
    assert isinstance(target, ConnectorTargetInterface), "DevoTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True