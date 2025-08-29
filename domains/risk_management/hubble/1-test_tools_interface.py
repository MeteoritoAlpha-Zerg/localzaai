# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    hubble_url = zerg_state.get("hubble_url").get("value")
    hubble_api_key = zerg_state.get("hubble_api_key", {}).get("value")
    hubble_client_id = zerg_state.get("hubble_client_id", {}).get("value")
    hubble_client_secret = zerg_state.get("hubble_client_secret", {}).get("value")

    from connectors.hubble.config import HubbleConnectorConfig
    from connectors.hubble.connector import HubbleConnector
    from connectors.hubble.target import HubbleTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config - prefer API key over OAuth
    if hubble_api_key:
        config = HubbleConnectorConfig(
            url=hubble_url,
            api_key=hubble_api_key,
        )
    elif hubble_client_id and hubble_client_secret:
        config = HubbleConnectorConfig(
            url=hubble_url,
            client_id=hubble_client_id,
            client_secret=hubble_client_secret,
        )
    else:
        raise Exception("Either hubble_api_key or both hubble_client_id and hubble_client_secret must be provided")

    assert isinstance(config, ConnectorConfig), "HubbleConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = HubbleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "HubbleConnector should be of type Connector"

    target = HubbleTarget()
    assert isinstance(target, ConnectorTargetInterface), "HubbleTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True