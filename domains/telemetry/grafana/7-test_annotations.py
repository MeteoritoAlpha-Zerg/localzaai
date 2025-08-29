# 7-test_annotations.py

async def test_annotations(zerg_state=None):
    """Test Grafana annotations retrieval with time range and tag filtering"""
    print("Attempting to authenticate using Grafana connector")

    assert zerg_state, "this test requires valid zerg_state"

    grafana_url = zerg_state.get("grafana_url").get("value")
    grafana_api_key = zerg_state.get("grafana_api_key", {}).get("value")
    grafana_username = zerg_state.get("grafana_username", {}).get("value")
    grafana_password = zerg_state.get("grafana_password", {}).get("value")
    grafana_org_id = int(zerg_state.get("grafana_org_id", {}).get("value", 1))
    grafana_default_time_range = zerg_state.get("grafana_default_time_range", {}).get("value", "1h")

    from connectors.grafana.config import GrafanaConnectorConfig
    from connectors.grafana.connector import GrafanaConnector
    from connectors.grafana.tools import GrafanaConnectorTools, GetGrafanaAnnotationsInput
    from connectors.grafana.target import GrafanaTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    from datetime import datetime, timedelta

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

    # find the get_grafana_annotations tool and execute it
    get_annotations_tool = next((tool for tool in tools if tool.name == "get_grafana_annotations"), None)
    assert get_annotations_tool, "get_grafana_annotations tool not found in available tools"
    
    # Set up the time range based on the default time range
    end_time = datetime.now()
    
    # Parse the time range string for a longer period to catch more annotations
    if grafana_default_time_range.endswith('h'):
        hours = int(grafana_default_time_range[:-1])
        # Extend the range to increase chances of finding annotations
        start_time = end_time - timedelta(hours=hours * 24)  # Look back 24x the default range
    elif grafana_default_time_range.endswith('m'):
        minutes = int(grafana_default_time_range[:-1])
        start_time = end_time - timedelta(hours=24)  # Look back 24 hours
    elif grafana_default_time_range.endswith('d'):
        days = int(grafana_default_time_range[:-1])
        start_time = end_time - timedelta(days=days * 7)  # Look back 7x the default range
    else:
        # Default to 24 hours
        start_time = end_time - timedelta(hours=24)
    
    print(f"Querying annotations from {start_time.isoformat()} to {end_time.isoformat()}")
    
    # Execute the tool to retrieve annotations for the specified time range
    annotations_result = await get_annotations_tool.execute(
        start_time=int(start_time.timestamp() * 1000),  # Convert to milliseconds
        end_time=int(end_time.timestamp() * 1000),      # Convert to milliseconds
        dashboard_uid=dashboard_uid,
        limit=100
    )
    
    annotations = annotations_result.raw_result
    
    print("Type of returned annotations:", type(annotations))
    
    # Verify that annotations is a list
    assert isinstance(annotations, list), "annotations should be a list"
    print(f"Retrieved {len(annotations)} annotations")
    
    # If there are annotations, verify their structure
    if annotations:
        # Check structure of some annotations
        annotations_to_check = annotations[:5] if len(annotations) > 5 else annotations
        
        for annotation in annotations_to_check:
            assert isinstance(annotation, dict), "Each annotation should be a dictionary"
            
            # Verify essential annotation fields
            assert "id" in annotation, "Each annotation should have an 'id' field"
            assert "time" in annotation, "Each annotation should have a 'time' field"
            assert "text" in annotation, "Each annotation should have a 'text' field"
            
            # Verify time is within requested range
            annotation_time = annotation["time"]
            if isinstance(annotation_time, str):
                # Parse ISO format if time is a string
                annotation_dt = datetime.fromisoformat(annotation_time.replace('Z', '+00:00'))
                annotation_timestamp = annotation_dt.timestamp() * 1000
            else:
                # Assume it's already a timestamp in milliseconds
                annotation_timestamp = annotation_time
                annotation_dt = datetime.fromtimestamp(annotation_timestamp / 1000)
            
            assert start_time.timestamp() * 1000 <= annotation_timestamp <= end_time.timestamp() * 1000, \
                f"Annotation timestamp {annotation_dt} is outside requested range"
            
            print(f"  Annotation ID: {annotation['id']}")
            print(f"  Time: {annotation_dt}")
            print(f"  Text: {annotation['text'][:100]}...")  # Truncate long text
            
            # Check for optional fields
            if "tags" in annotation:
                assert isinstance(annotation["tags"], list), "Tags should be a list"
                print(f"  Tags: {annotation['tags']}")
            
            if "dashboardUID" in annotation:
                assert isinstance(annotation["dashboardUID"], str), "dashboardUID should be a string"
                print(f"  Dashboard UID: {annotation['dashboardUID']}")
            
            if "panelId" in annotation:
                assert isinstance(annotation["panelId"], (int, type(None))), "panelId should be an integer or None"
                if annotation["panelId"] is not None:
                    print(f"  Panel ID: {annotation['panelId']}")
            
            if "userId" in annotation:
                assert isinstance(annotation["userId"], (int, type(None))), "userId should be an integer or None"
            
            if "timeEnd" in annotation:
                # Check time range annotations
                time_end = annotation["timeEnd"]
                if time_end:
                    if isinstance(time_end, str):
                        time_end_dt = datetime.fromisoformat(time_end.replace('Z', '+00:00'))
                    else:
                        time_end_dt = datetime.fromtimestamp(time_end / 1000)
                    
                    assert annotation_dt <= time_end_dt, "Annotation start time should be before or equal to end time"
                    print(f"  Time Range: {annotation_dt} to {time_end_dt}")
        
        # Log the structure of the first annotation for debugging
        print(f"Example annotation structure: {annotations[0]}")
        
        # Test filtering by tags if annotations have tags
        annotations_with_tags = [ann for ann in annotations if ann.get("tags")]
        if annotations_with_tags:
            # Get unique tags from the annotations
            all_tags = set()
            for ann in annotations_with_tags:
                all_tags.update(ann.get("tags", []))
            
            if all_tags:
                # Test filtering by a specific tag
                test_tag = list(all_tags)[0]
                print(f"Testing tag filtering with tag: {test_tag}")
                
                tagged_annotations_result = await get_annotations_tool.execute(
                    start_time=int(start_time.timestamp() * 1000),
                    end_time=int(end_time.timestamp() * 1000),
                    tags=[test_tag],
                    limit=50
                )
                
                tagged_annotations = tagged_annotations_result.raw_result
                assert isinstance(tagged_annotations, list), "Tagged annotations should be a list"
                
                # Verify that all returned annotations have the requested tag
                for ann in tagged_annotations:
                    assert test_tag in ann.get("tags", []), f"Annotation should have tag '{test_tag}'"
                
                print(f"Found {len(tagged_annotations)} annotations with tag '{test_tag}'")
    else:
        print("No annotations found for the specified time range")
        print("This is normal if the Grafana instance doesn't have any annotations yet")
    
    # Verify the tool works even if no annotations are found (should return empty list, not error)
    assert annotations is not None, "Annotations retrieval tool should return a list (even if empty) not None"

    print(f"Successfully tested annotations retrieval for Grafana dashboard: {dashboard_uid}")

    return True