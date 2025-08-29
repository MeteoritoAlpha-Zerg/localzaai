# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""

    from pydantic import SecretStr

    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    sharepoint_url = zerg_state.get("sharepoint_url").get("value")
    sharepoint_client_id = zerg_state.get("sharepoint_client_id").get("value")
    sharepoint_client_secret = zerg_state.get("sharepoint_client_secret").get("value")
    sharepoint_tenant_id = zerg_state.get("sharepoint_tenant_id").get("value")

    from connectors.sharepoint.config import SharePointConnectorConfig
    from connectors.sharepoint.connector import SharePointConnector
    from connectors.sharepoint.target import SharePointTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    # Note this is common code
    from common.models.tool import Tool

    config = SharePointConnectorConfig(
        url=sharepoint_url,
        client_id=sharepoint_client_id,
        client_secret=sharepoint_client_secret,
        tenant_id=sharepoint_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "SharepointConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = SharePointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SharePointConnector should be of type Connector"

    target = SharePointTarget()
    assert isinstance(target, ConnectorTargetInterface), "SharePointTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True