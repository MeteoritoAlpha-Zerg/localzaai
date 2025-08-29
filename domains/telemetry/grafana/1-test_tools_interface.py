# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    grafana_url = zerg_state.get("grafana_url").get("value")
    grafana_api_key = zerg_state.get("grafana_api_key", {}).get("value")
    grafana_username = zerg_state.get("grafana_username", {}).get("value")
    grafana_password = zerg_state.get("grafana_password", {}).get("value")
    grafana_org_id = int(zerg_state.get("grafana_org_id", {}).get("value", 1))

    from connectors.grafana.config import GrafanaConnectorConfig
    from connectors.grafana.connector import GrafanaConnector
    from connectors.grafana.target import GrafanaTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

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

    target = GrafanaTarget()
    assert isinstance(target, ConnectorTargetInterface), "GrafanaTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True