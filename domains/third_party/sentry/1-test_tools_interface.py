# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    sentry_api_token = zerg_state.get("sentry_api_token").get("value")
    sentry_organization_slug = zerg_state.get("sentry_organization_slug").get("value")
    sentry_base_url = zerg_state.get("sentry_base_url").get("value")

    from connectors.sentry.config import SentryConnectorConfig
    from connectors.sentry.connector import SentryConnector
    from connectors.sentry.target import SentryTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from common.models.tool import Tool

    config = SentryConnectorConfig(
        api_token=sentry_api_token,
        organization_slug=sentry_organization_slug,
        base_url=sentry_base_url,
    )
    assert isinstance(config, ConnectorConfig), "SentryConnectorConfig should be of type ConnectorConfig"

    connector = SentryConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SentryConnector should be of type Connector"

    target = SentryTarget()
    assert isinstance(target, ConnectorTargetInterface), "SentryTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True