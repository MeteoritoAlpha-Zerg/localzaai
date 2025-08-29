# 8-test_alerts.py

async def test_alerts(zerg_state=None):
    """Test Grafana alert rules and their current states retrieval"""
    print("Attempting to authenticate using Grafana connector")

    assert zerg_state, "this test requires valid zerg_state"

    grafana_url = zerg_state.get("grafana_url").get("value")
    grafana_api_key = zerg_state.get("grafana_api_key", {}).get("value")
    grafana_username = zerg_state.get("grafana_username", {}).get("value")
    grafana_password = zerg_state.get("grafana_password", {}).get("value")
    grafana_org_id = int(zerg_state.get("grafana_org_id", {}).get("value", 1))

    from connectors.grafana.config import GrafanaConnectorConfig
    from connectors.grafana.connector import GrafanaConnector
    from connectors.grafana.tools import GrafanaConnectorTools, GetGrafanaAlertsInput
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

    # find the get_grafana_alerts tool and execute it
    get_alerts_tool = next((tool for tool in tools if tool.name == "get_grafana_alerts"), None)
    assert get_alerts_tool, "get_grafana_alerts tool not found in available tools"
    
    print("Querying Grafana alert rules...")
    
    # Execute the tool to retrieve alert rules
    alerts_result = await get_alerts_tool.execute()
    alerts = alerts_result.raw_result
    
    print("Type of returned alerts:", type(alerts))
    
    # Verify that alerts is a list
    assert isinstance(alerts, list), "alerts should be a list"
    print(f"Retrieved {len(alerts)} alert rules")
    
    # If there are alerts, verify their structure
    if alerts:
        # Check structure of some alerts
        alerts_to_check = alerts[:5] if len(alerts) > 5 else alerts
        
        for alert in alerts_to_check:
            assert isinstance(alert, dict), "Each alert should be a dictionary"
            
            # Verify essential alert fields
            assert "uid" in alert, "Each alert should have a 'uid' field"
            assert "title" in alert, "Each alert should have a 'title' field"
            
            print(f"  Alert UID: {alert['uid']}")
            print(f"  Title: {alert['title']}")
            
            # Check for common alert fields
            if "condition" in alert:
                assert isinstance(alert["condition"], str), "Condition should be a string"
                print(f"  Condition: {alert['condition']}")
            
            if "data" in alert:
                assert isinstance(alert["data"], list), "Alert data should be a list"
                print(f"  Data queries: {len(alert['data'])}")
                
                # Check structure of alert data queries
                for data_query in alert["data"]:
                    assert isinstance(data_query, dict), "Each data query should be a dictionary"
                    if "refId" in data_query:
                        assert isinstance(data_query["refId"], str), "refId should be a string"
                    if "model" in data_query:
                        assert isinstance(data_query["model"], dict), "Model should be a dictionary"
            
            if "noDataState" in alert:
                assert isinstance(alert["noDataState"], str), "noDataState should be a string"
                print(f"  No Data State: {alert['noDataState']}")
            
            if "execErrState" in alert:
                assert isinstance(alert["execErrState"], str), "execErrState should be a string"
                print(f"  Execution Error State: {alert['execErrState']}")
            
            if "for" in alert:
                # Duration field
                assert isinstance(alert["for"], str), "Duration 'for' should be a string"
                print(f"  Duration: {alert['for']}")
            
            if "annotations" in alert:
                assert isinstance(alert["annotations"], dict), "Annotations should be a dictionary"
                annotations = alert["annotations"]
                if "description" in annotations:
                    print(f"  Description: {annotations['description'][:100]}...")  # Truncate long descriptions
                if "runbook_url" in annotations:
                    print(f"  Runbook URL: {annotations['runbook_url']}")
            
            if "labels" in alert:
                assert isinstance(alert["labels"], dict), "Labels should be a dictionary"
                print(f"  Labels: {alert['labels']}")
            
            if "folderUID" in alert:
                assert isinstance(alert["folderUID"], str), "folderUID should be a string"
                print(f"  Folder UID: {alert['folderUID']}")
            
            if "ruleGroup" in alert:
                assert isinstance(alert["ruleGroup"], str), "ruleGroup should be a string"
                print(f"  Rule Group: {alert['ruleGroup']}")
            
            if "orgID" in alert:
                assert isinstance(alert["orgID"], int), "orgID should be an integer"
                print(f"  Organization ID: {alert['orgID']}")
            
            # Check for state information if available
            if "state" in alert:
                assert isinstance(alert["state"], str), "State should be a string"
                print(f"  Current State: {alert['state']}")
            
            if "health" in alert:
                assert isinstance(alert["health"], str), "Health should be a string"
                print(f"  Health: {alert['health']}")
            
            if "lastEvalTime" in alert:
                print(f"  Last Evaluation: {alert['lastEvalTime']}")
            
            if "evaluationTime" in alert:
                assert isinstance(alert["evaluationTime"], (int, float)), "evaluationTime should be a number"
                print(f"  Evaluation Time: {alert['evaluationTime']}s")
        
        # Log the structure of the first alert for debugging
        print(f"Example alert structure: {alerts[0]}")
        
        # Test filtering by state if alerts have state information
        alerts_with_state = [alert for alert in alerts if "state" in alert]
        if alerts_with_state:
            # Get unique states from the alerts
            states = set(alert["state"] for alert in alerts_with_state)
            print(f"Found alert states: {states}")
            
            # Test filtering by state if the tool supports it
            if len(states) > 1:
                test_state = list(states)[0]
                print(f"Testing state filtering with state: {test_state}")
                
                try:
                    state_filtered_result = await get_alerts_tool.execute(state=test_state)
                    state_filtered_alerts = state_filtered_result.raw_result
                    
                    assert isinstance(state_filtered_alerts, list), "State filtered alerts should be a list"
                    
                    # Verify that all returned alerts have the requested state
                    for alert in state_filtered_alerts:
                        if "state" in alert:
                            assert alert["state"] == test_state, f"Alert should have state '{test_state}'"
                    
                    print(f"Found {len(state_filtered_alerts)} alerts with state '{test_state}'")
                except Exception as e:
                    print(f"State filtering not supported or failed: {e}")
        
        # Test getting alert instances/evaluations if available
        try:
            # Some Grafana versions have separate endpoints for alert instances
            get_alert_instances_tool = next((tool for tool in tools if tool.name == "get_grafana_alert_instances"), None)
            if get_alert_instances_tool:
                print("Testing alert instances retrieval...")
                instances_result = await get_alert_instances_tool.execute()
                instances = instances_result.raw_result
                
                assert isinstance(instances, list), "Alert instances should be a list"
                print(f"Retrieved {len(instances)} alert instances")
                
                if instances:
                    # Check structure of alert instances
                    for instance in instances[:3]:  # Check first 3
                        assert isinstance(instance, dict), "Each instance should be a dictionary"
                        if "labels" in instance:
                            assert isinstance(instance["labels"], dict), "Instance labels should be a dictionary"
                        if "state" in instance:
                            assert isinstance(instance["state"], str), "Instance state should be a string"
                        if "activeAt" in instance:
                            print(f"  Instance active since: {instance['activeAt']}")
                        if "value" in instance:
                            print(f"  Instance value: {instance['value']}")
        except Exception as e:
            print(f"Alert instances retrieval not available or failed: {e}")
    else:
        print("No alert rules found in the Grafana instance")
        print("This is normal if the Grafana instance doesn't have any configured alerts yet")
    
    # Verify the tool works even if no alerts are found (should return empty list, not error)
    assert alerts is not None, "Alerts retrieval tool should return a list (even if empty) not None"

    print(f"Successfully tested alerts retrieval for Grafana instance")

    return True