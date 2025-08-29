# 3-test_query_target_options.py

async def test_organization_project_enumeration_options(zerg_state=None):
    """Test Sentry organization and project enumeration by way of query target options"""
    print("Attempting to authenticate using Sentry connector")

    assert zerg_state, "this test requires valid zerg_state"

    sentry_api_token = zerg_state.get("sentry_api_token").get("value")
    sentry_organization_slug = zerg_state.get("sentry_organization_slug").get("value")
    sentry_base_url = zerg_state.get("sentry_base_url").get("value")

    from connectors.sentry.config import SentryConnectorConfig
    from connectors.sentry.connector import SentryConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

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

    sentry_query_target_options = await connector.get_query_target_options()
    assert isinstance(sentry_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert sentry_query_target_options, "Failed to retrieve query target options"

    print(f"Sentry query target option definitions: {sentry_query_target_options.definitions}")
    print(f"Sentry query target option selectors: {sentry_query_target_options.selectors}")

    return True