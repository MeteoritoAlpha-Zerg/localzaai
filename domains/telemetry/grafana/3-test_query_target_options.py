# 3-test_query_target_options.py

async def test_dashboard_enumeration_options(zerg_state=None):
    """Test Grafana dashboard enumeration by way of query target options"""
    print("Attempting to authenticate using Grafana connector")

    assert zerg_state, "this test requires valid zerg_state"

    grafana_url = zerg_state.get("grafana_url").get("value")
    grafana_api_key = zerg_state.get("grafana_api_key", {}).get("value")
    grafana_username = zerg_state.get("grafana_username", {}).get("value")
    grafana_password = zerg_state.get("grafana_password", {}).get("value")
    grafana_org_id = int(zerg_state.get("grafana_org_id", {}).get("value", 1))

    from connectors.grafana.config import GrafanaConnectorConfig
    from connectors.grafana.connector import GrafanaConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = GrafanaConnectorConfig(
        url=grafana_url,
        api_key=grafana_api_key,
        username=grafana_username,
        password=grafana_password,
        org_id=grafana_org_id,
    )
    assert isinstance(config, ConnectorConfig), "GrafanaConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = GrafanaConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GrafanaConnector should be of type Connector"

    query_target_options = await connector.get_query_target_options()
    assert isinstance(query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert query_target_options, "Failed to retrieve query target options"

    print(f"grafana query target option definitions: {query_target_options.definitions}")
    print(f"grafana query target option selectors: {query_target_options.selectors}")

    return True