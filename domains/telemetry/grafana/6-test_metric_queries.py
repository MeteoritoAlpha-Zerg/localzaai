# 6-test_metric_queries.py

async def test_metric_queries(zerg_state=None):
    """Test Grafana data source queries with specified queries, filters, and time ranges"""
    print("Attempting to authenticate using Grafana connector")

    assert zerg_state, "this test requires valid zerg_state"

    grafana_url = zerg_state.get("grafana_url").get("value")
    grafana_api_key = zerg_state.get("grafana_api_key", {}).get("value")
    grafana_username = zerg_state.get("grafana_username", {}).get("value")
    grafana_password = zerg_state.get("grafana_password", {}).get("value")
    grafana_org_id = int(zerg_state.get("grafana_org_id", {}).get("value", 1))
    grafana_default_time_range = zerg_state.get("grafana_default_time_range", {}).get("value", "1h")
    grafana_max_data_points = int(zerg_state.get("grafana_max_data_points", {}).get("value", 1000))

    from connectors.grafana.config import GrafanaConnectorConfig
    from connectors.grafana.connector import GrafanaConnector
    from connectors.grafana.tools import GrafanaConnectorTools, QueryGrafanaMetricsInput
    from connectors.grafana.target import GrafanaTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    from datetime import datetime, timedelta
    import time

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

    # Get the get_grafana_datasources tool first to find available data sources
    get_datasources_tool = next((tool for tool in tools if tool.name == "get_grafana_datasources"), None)
    assert get_datasources_tool, "get_grafana_datasources tool not found in available tools"
    
    datasources_result = await get_datasources_tool.execute()
    datasources = datasources_result.raw_result
    
    assert isinstance(datasources, list), "datasources should be a list"
    assert len(datasources) > 0, "datasources should not be empty"
    
    # Select a data source for querying (prefer TestData if available)
    test_datasource = None
    for ds in datasources:
        if ds.get("type") == "testdata":
            test_datasource = ds
            break
    
    # If no TestData source found, use the first available
    if not test_datasource:
        test_datasource = datasources[0]
    
    datasource_uid = test_datasource["uid"]
    datasource_name = test_datasource["name"]
    datasource_type = test_datasource["type"]
    
    print(f"Selected data source for testing: {datasource_name} (Type: {datasource_type}, UID: {datasource_uid})")
    
    # find the query_grafana_metrics tool
    query_metrics_tool = next((tool for tool in tools if tool.name == "query_grafana_metrics"), None)
    assert query_metrics_tool, "query_grafana_metrics tool not found in available tools"
    
    # Set up the time range based on the default time range
    end_time = datetime.now()
    
    # Parse the time range string
    if grafana_default_time_range.endswith('h'):
        hours = int(grafana_default_time_range[:-1])
        start_time = end_time - timedelta(hours=hours)
    elif grafana_default_time_range.endswith('m'):
        minutes = int(grafana_default_time_range[:-1])
        start_time = end_time - timedelta(minutes=minutes)
    elif grafana_default_time_range.endswith('d'):
        days = int(grafana_default_time_range[:-1])
        start_time = end_time - timedelta(days=days)
    else:
        # Default to 1 hour
        start_time = end_time - timedelta(hours=1)
    
    # Define query based on data source type
    query_config = {
        "datasource": {
            "uid": datasource_uid,
            "type": datasource_type
        },
        "refId": "A"
    }
    
    if datasource_type == "testdata":
        # Use TestData plugin scenario
        query_config.update({
            "scenarioId": "random_walk",
            "seriesCount": 1,
            "alias": "Test Metric"
        })
    elif datasource_type == "prometheus":
        # Use a basic Prometheus query
        query_config["expr"] = "up"
    elif datasource_type == "influxdb":
        # Use a basic InfluxDB query
        query_config["query"] = "SELECT mean(value) FROM cpu"
    else:
        # Generic query for other data sources
        query_config["rawSql"] = "SELECT 1 as value, NOW() as time"
    
    print(f"Querying data source {datasource_name} with query config: {query_config}")
    
    # Execute the tool to query the selected data source
    query_result = await query_metrics_tool.execute(
        datasource_uid=datasource_uid,
        query=query_config,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        max_data_points=grafana_max_data_points
    )
    
    metric_data = query_result.raw_result
    
    # Verify the structure of the response
    assert isinstance(metric_data, dict), "metric_data should be a dictionary"
    print(f"Received metric data with keys: {list(metric_data.keys())}")
    
    # Verify required fields in the response
    assert "data" in metric_data, "Response should include a 'data' field"
    data = metric_data["data"]
    assert isinstance(data, list), "Data should be a list of series"
    
    # If we have data, check the structure
    if len(data) > 0:
        print(f"Retrieved {len(data)} data series")
        
        for series_idx, series in enumerate(data):
            assert isinstance(series, dict), f"Series {series_idx} should be a dictionary"
            
            # Check for common series fields
            if "target" in series:
                assert isinstance(series["target"], str), "Series target should be a string"
                print(f"  Series {series_idx}: {series['target']}")
            
            if "datapoints" in series:
                datapoints = series["datapoints"]
                assert isinstance(datapoints, list), "Datapoints should be a list"
                print(f"    Data points: {len(datapoints)}")
                
                # Check structure of some data points
                points_to_check = datapoints[:3] if len(datapoints) > 3 else datapoints
                
                for point in points_to_check:
                    assert isinstance(point, list), "Each data point should be a list [value, timestamp]"
                    assert len(point) >= 2, "Each data point should have at least value and timestamp"
                    
                    value, timestamp = point[0], point[1]
                    
                    # Value can be number or null
                    assert isinstance(value, (int, float)) or value is None, \
                        f"Data point value should be a number or None, got {type(value)}"
                    
                    # Timestamp should be a number (Unix timestamp in milliseconds)
                    assert isinstance(timestamp, (int, float)), \
                        f"Data point timestamp should be a number, got {type(timestamp)}"
                    
                    # Verify timestamp is within reasonable range (not too old or in future)
                    timestamp_dt = datetime.fromtimestamp(timestamp / 1000)
                    assert start_time <= timestamp_dt <= end_time + timedelta(minutes=5), \
                        f"Timestamp {timestamp_dt} is outside the expected range"
                
                # Check that timestamps are in ascending order
                if len(datapoints) > 1:
                    for i in range(1, len(datapoints)):
                        prev_ts = datapoints[i-1][1]
                        curr_ts = datapoints[i][1]
                        assert prev_ts <= curr_ts, "Timestamps should be in ascending order"
            
            elif "fields" in series:
                # Handle field-based response format (newer Grafana versions)
                fields = series["fields"]
                assert isinstance(fields, list), "Fields should be a list"
                
                for field in fields:
                    assert isinstance(field, dict), "Each field should be a dictionary"
                    assert "name" in field, "Each field should have a name"
                    if "values" in field:
                        assert isinstance(field["values"], list), "Field values should be a list"
                
                print(f"    Fields: {[field['name'] for field in fields]}")
    else:
        print("No data returned for the specified time range and query")
    
    # Verify metadata if present
    if "status" in metric_data:
        assert isinstance(metric_data["status"], str), "Status should be a string"
        print(f"Query status: {metric_data['status']}")
    
    if "message" in metric_data:
        assert isinstance(metric_data["message"], str), "Message should be a string"
    
    print(f"Successfully tested metric queries for Grafana data source: {datasource_name}")
    
    return True