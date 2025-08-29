# 5-test_dashboard_retrieval.py

async def test_dashboard_retrieval(zerg_state=None):
    """Test Grafana dashboard configuration and panel data retrieval for a selected dashboard"""
    print("Attempting to authenticate using Grafana connector")

    assert zerg_state, "this test requires valid zerg_state"

    grafana_url = zerg_state.get("grafana_url").get("value")
    grafana_api_key = zerg_state.get("grafana_api_key", {}).get("value")
    grafana_username = zerg_state.get("grafana_username", {}).get("value")
    grafana_password = zerg_state.get("grafana_password", {}).get("value")
    grafana_org_id = int(zerg_state.get("grafana_org_id", {}).get("value", 1))

    from connectors.grafana.config import GrafanaConnectorConfig
    from connectors.grafana.connector import GrafanaConnector
    from connectors.grafana.tools import GrafanaConnectorTools, GetGrafanaDashboardInput
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
    dashboard_uid = dashboard_selector.values[0] if dashboard_selector.values else None
    print(f"Selected dashboard for testing: {dashboard_uid}")
    assert dashboard_uid, "failed to retrieve dashboard from dashboard selector"

    # set up the target with selected dashboard
    target = GrafanaTarget(dashboards=[dashboard_uid])
    assert isinstance(target, ConnectorTargetInterface), "GrafanaTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # find the get_grafana_dashboard tool and execute it
    get_dashboard_tool = next((tool for tool in tools if tool.name == "get_grafana_dashboard"), None)
    assert get_dashboard_tool, "get_grafana_dashboard tool not found in available tools"
    
    # Execute the tool to retrieve dashboard configuration for the selected dashboard
    dashboard_result = await get_dashboard_tool.execute(
        dashboard_uid=dashboard_uid
    )
    dashboard_data = dashboard_result.raw_result

    print("Type of returned dashboard data:", type(dashboard_data))
    
    # Verify that dashboard_data is a dictionary
    assert isinstance(dashboard_data, dict), "dashboard data should be a dictionary"
    print(f"Retrieved dashboard configuration for: {dashboard_uid}")
    
    # Verify essential dashboard fields
    assert "dashboard" in dashboard_data, "Response should contain a 'dashboard' field"
    dashboard = dashboard_data["dashboard"]
    
    assert isinstance(dashboard, dict), "Dashboard should be a dictionary"
    assert "uid" in dashboard, "Dashboard should have a 'uid' field"
    assert "title" in dashboard, "Dashboard should have a 'title' field"
    assert "panels" in dashboard, "Dashboard should have a 'panels' field"
    
    # Verify the dashboard UID matches what we requested
    assert dashboard["uid"] == dashboard_uid, \
        f"Retrieved dashboard UID {dashboard['uid']} does not match requested UID {dashboard_uid}"
    
    print(f"Dashboard title: {dashboard['title']}")
    print(f"Dashboard UID: {dashboard['uid']}")
    print(f"Number of panels: {len(dashboard['panels'])}")
    
    # Verify panels structure
    panels = dashboard["panels"]
    assert isinstance(panels, list), "Panels should be a list"
    
    if panels:
        # Check structure of some panels
        panels_to_check = panels[:3] if len(panels) > 3 else panels
        
        for panel in panels_to_check:
            assert isinstance(panel, dict), "Each panel should be a dictionary"
            assert "id" in panel, "Each panel should have an 'id' field"
            assert "title" in panel, "Each panel should have a 'title' field"
            assert "type" in panel, "Each panel should have a 'type' field"
            
            print(f"  Panel: {panel['title']} (Type: {panel['type']}, ID: {panel['id']})")
            
            # Check for common panel fields
            if "targets" in panel:
                assert isinstance(panel["targets"], list), "Panel targets should be a list"
                for target in panel["targets"]:
                    assert isinstance(target, dict), "Each target should be a dictionary"
                    if "refId" in target:
                        assert isinstance(target["refId"], str), "refId should be a string"
            
            if "gridPos" in panel:
                assert isinstance(panel["gridPos"], dict), "gridPos should be a dictionary"
                grid_pos = panel["gridPos"]
                for pos_field in ["h", "w", "x", "y"]:
                    if pos_field in grid_pos:
                        assert isinstance(grid_pos[pos_field], int), f"gridPos.{pos_field} should be an integer"
        
        # Log the structure of the first panel for debugging
        print(f"Example panel structure: {panels[0]}")
    else:
        print("Dashboard has no panels")
    
    # Check for other common dashboard fields
    if "time" in dashboard:
        assert isinstance(dashboard["time"], dict), "Dashboard time should be a dictionary"
        time_config = dashboard["time"]
        if "from" in time_config:
            assert isinstance(time_config["from"], str), "time.from should be a string"
        if "to" in time_config:
            assert isinstance(time_config["to"], str), "time.to should be a string"
    
    if "tags" in dashboard:
        assert isinstance(dashboard["tags"], list), "Dashboard tags should be a list"
    
    if "version" in dashboard:
        assert isinstance(dashboard["version"], int), "Dashboard version should be an integer"
    
    # Check metadata fields
    if "meta" in dashboard_data:
        meta = dashboard_data["meta"]
        assert isinstance(meta, dict), "Meta should be a dictionary"
        if "slug" in meta:
            assert isinstance(meta["slug"], str), "Meta slug should be a string"
        if "url" in meta:
            assert isinstance(meta["url"], str), "Meta URL should be a string"

    print(f"Successfully tested dashboard retrieval for Grafana dashboard: {dashboard_uid}")

    return True