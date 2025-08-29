# 4-test_list_datasources.py

async def test_list_datasources(zerg_state=None):
    """Test Grafana data sources enumeration through connector tools"""
    print("Attempting to authenticate using Grafana connector")

    assert zerg_state, "this test requires valid zerg_state"

    grafana_url = zerg_state.get("grafana_url").get("value")
    grafana_api_key = zerg_state.get("grafana_api_key", {}).get("value")
    grafana_username = zerg_state.get("grafana_username", {}).get("value")
    grafana_password = zerg_state.get("grafana_password", {}).get("value")
    grafana_org_id = int(zerg_state.get("grafana_org_id", {}).get("value", 1))

    from connectors.grafana.config import GrafanaConnectorConfig
    from connectors.grafana.connector import GrafanaConnector
    from connectors.grafana.tools import GrafanaConnectorTools
    from connectors.grafana.target import GrafanaTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = GrafanaConnectorConfig(
        url=grafana_url,
        api_key=grafana_api_key,
        username=grafana_username,
        password=grafana_password,
        org_id=grafana_org_id,
    )
    assert isinstance(config, ConnectorConfig), "GrafanaConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = GrafanaConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GrafanaConnector should be of type Connector"

    # get query target options to find available dashboards
    grafana_query_target_options = await connector.get_query_target_options()
    assert isinstance(grafana_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select dashboards to target
    dashboard_selector = None
    for selector in grafana_query_target_options.selectors:
        if selector.type == 'dashboards':  
            dashboard_selector = selector
            break

    assert dashboard_selector, "failed to retrieve dashboard selector from query target options"
    assert isinstance(dashboard_selector.values, list), "dashboard_selector values must be a list"
    
    # Select the first dashboard for testing
    dashboard = dashboard_selector.values[0] if dashboard_selector.values else None
    print(f"Selected dashboard for testing: {dashboard}")
    assert dashboard, "failed to retrieve dashboard from dashboard selector"

    # set up the target with selected dashboard
    target = GrafanaTarget(dashboards=[dashboard])
    assert isinstance(target, ConnectorTargetInterface), "GrafanaTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # find the get_grafana_datasources tool and execute it
    get_datasources_tool = next((tool for tool in tools if tool.name == "get_grafana_datasources"), None)
    assert get_datasources_tool, "get_grafana_datasources tool not found in available tools"
    
    datasources_result = await get_datasources_tool.execute()
    datasources = datasources_result.raw_result

    print("Type of returned datasources:", type(datasources))
    print(f"Number of data sources: {len(datasources)}")
    
    # Verify that datasources is a list
    assert isinstance(datasources, list), "datasources should be a list"
    assert len(datasources) > 0, "datasources should not be empty"
    
    # Check the structure of the datasources list
    for datasource in datasources:
        print(f"Data source: {datasource.get('name', 'Unknown')} (Type: {datasource.get('type', 'Unknown')})")
        assert isinstance(datasource, dict), "Each datasource should be a dictionary"
        
        # Verify essential datasource fields
        assert "uid" in datasource, "Each datasource should have a 'uid' field"
        assert "name" in datasource, "Each datasource should have a 'name' field"
        assert "type" in datasource, "Each datasource should have a 'type' field"
        
        # Check for common optional fields
        if "url" in datasource:
            assert isinstance(datasource["url"], str), "URL should be a string"
        if "access" in datasource:
            assert isinstance(datasource["access"], str), "Access should be a string"
        if "isDefault" in datasource:
            assert isinstance(datasource["isDefault"], bool), "isDefault should be a boolean"
        
        print(f"  - UID: {datasource['uid']}")
        print(f"  - Name: {datasource['name']}")
        print(f"  - Type: {datasource['type']}")
        if "url" in datasource and datasource["url"]:
            print(f"  - URL: {datasource['url']}")
        
    # Log the structure of the first datasource for debugging
    if datasources:
        print(f"Example datasource structure: {datasources[0]}")

    print(f"Successfully retrieved and validated Grafana data sources: {len(datasources)} found")

    return True