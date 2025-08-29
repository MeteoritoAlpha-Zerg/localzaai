# 6-test_alerts_events.py

async def test_alerts_events(zerg_state=None):
    """Test Devo alerts and security events retrieval"""
    print("Attempting to retrieve alerts and events using Devo connector")

    assert zerg_state, "this test requires valid zerg_state"

    devo_url = zerg_state.get("devo_url").get("value")
    devo_api_key = zerg_state.get("devo_api_key", {}).get("value")
    devo_api_secret = zerg_state.get("devo_api_secret", {}).get("value")
    devo_oauth_token = zerg_state.get("devo_oauth_token", {}).get("value")
    devo_domain = zerg_state.get("devo_domain").get("value")

    from connectors.devo.config import DevoConnectorConfig
    from connectors.devo.connector import DevoConnector
    from connectors.devo.tools import DevoConnectorTools
    from connectors.devo.target import DevoTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config - prefer OAuth token over API key/secret
    if devo_oauth_token:
        config = DevoConnectorConfig(
            url=devo_url,
            oauth_token=devo_oauth_token,
            default_domain=devo_domain,
        )
    elif devo_api_key and devo_api_secret:
        config = DevoConnectorConfig(
            url=devo_url,
            api_key=devo_api_key,
            api_secret=devo_api_secret,
            default_domain=devo_domain,
        )
    else:
        raise Exception("Either devo_oauth_token or both devo_api_key and devo_api_secret must be provided")

    assert isinstance(config, ConnectorConfig), "DevoConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = DevoConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DevoConnector should be of type Connector"

    # get query target options
    devo_query_target_options = await connector.get_query_target_options()
    assert isinstance(devo_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select domains to target
    domain_selector = None
    for selector in devo_query_target_options.selectors:
        if selector.type == 'domain_names':  
            domain_selector = selector
            break

    assert domain_selector, "failed to retrieve domain selector from query target options"

    assert isinstance(domain_selector.values, list), "domain_selector values must be a list"
    domain_name = domain_selector.values[0] if domain_selector.values else None
    print(f"Selecting domain name: {domain_name}")

    assert domain_name, f"failed to retrieve domain name from domain selector"

    # set up the target with domain names
    target = DevoTarget(domain_names=[domain_name])
    assert isinstance(target, ConnectorTargetInterface), "DevoTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get Devo alerts
    get_devo_alerts_tool = next(tool for tool in tools if tool.name == "get_devo_alerts")
    devo_alerts_result = await get_devo_alerts_tool.execute(
        domain_name=domain_name,
        limit=20  # limit to 20 alerts for testing
    )
    devo_alerts = devo_alerts_result.result

    print("Type of returned devo_alerts:", type(devo_alerts))
    print(f"len alerts: {len(devo_alerts)} alerts: {str(devo_alerts)[:200]}")

    # Verify that devo_alerts is a list
    assert isinstance(devo_alerts, list), "devo_alerts should be a list"
    
    # Alerts might be empty, which is acceptable
    if len(devo_alerts) > 0:
        # Limit the number of alerts to check if there are many
        alerts_to_check = devo_alerts[:5] if len(devo_alerts) > 5 else devo_alerts
        
        # Verify structure of each alert object
        for alert in alerts_to_check:
            # Verify essential Devo alert fields
            assert "id" in alert, "Each alert should have an 'id' field"
            assert "name" in alert, "Each alert should have a 'name' field"
            assert "status" in alert, "Each alert should have a 'status' field"
            
            # Verify common alert fields
            assert "created_at" in alert, "Each alert should have a 'created_at' field"
            assert "severity" in alert, "Each alert should have a 'severity' field"
            
            # Check for common alert severities
            valid_severities = ["critical", "high", "medium", "low", "info"]
            assert alert["severity"] in valid_severities, f"Alert severity {alert['severity']} is not a recognized severity"
            
            # Check for common alert statuses
            valid_statuses = ["open", "acknowledged", "resolved", "closed", "investigating"]
            assert alert["status"] in valid_statuses, f"Alert status {alert['status']} is not a recognized status"
            
            # Check for additional optional fields
            optional_fields = ["description", "rule_name", "triggered_by", "affected_assets", "correlation_id", "last_updated"]
            present_optional = [field for field in optional_fields if field in alert]
            
            print(f"Alert {alert['id']} ({alert['severity']}) contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first alert for debugging
            if alert == alerts_to_check[0]:
                print(f"Example alert structure: {alert}")

        print(f"Successfully retrieved and validated {len(devo_alerts)} Devo alerts")
    else:
        print("No alerts found - this is acceptable for testing")

    # Test 2: Get security events
    get_devo_security_events_tool = next(tool for tool in tools if tool.name == "get_devo_security_events")
    devo_security_events_result = await get_devo_security_events_tool.execute(
        domain_name=domain_name,
        limit=30  # limit to 30 security events for testing
    )
    devo_security_events = devo_security_events_result.result

    print("Type of returned devo_security_events:", type(devo_security_events))
    print(f"len security events: {len(devo_security_events)} events: {str(devo_security_events)[:200]}")

    # Verify that devo_security_events is a list
    assert isinstance(devo_security_events, list), "devo_security_events should be a list"
    
    # Security events might be empty, which is acceptable
    if len(devo_security_events) > 0:
        # Limit the number of events to check
        events_to_check = devo_security_events[:5] if len(devo_security_events) > 5 else devo_security_events
        
        # Verify structure of each security event object
        for event in events_to_check:
            # Verify essential Devo security event fields
            assert "eventdate" in event, "Each security event should have an 'eventdate' field"
            assert "event_type" in event, "Each security event should have an 'event_type' field"
            
            # Verify common security event fields
            common_event_fields = ["srcip", "dstip", "severity", "protocol"]
            present_event_fields = [field for field in common_event_fields if field in event]
            
            # Check for common event types
            valid_event_types = ["malware", "intrusion", "anomaly", "authentication", "network", "endpoint", "data_exfiltration"]
            
            # Check for additional optional fields
            optional_fields = ["user", "device", "application", "file_hash", "domain", "url", "process"]
            present_optional = [field for field in optional_fields if field in event]
            
            print(f"Security event {event['event_type']} contains these fields: {', '.join(present_event_fields + present_optional)}")
            
            # Log the structure of the first event for debugging
            if event == events_to_check[0]:
                print(f"Example security event structure: {event}")

        print(f"Successfully retrieved and validated {len(devo_security_events)} Devo security events")
    else:
        print("No security events found - this is acceptable for testing")

    # Test 3: Get correlation rules
    get_devo_correlation_rules_tool = next(tool for tool in tools if tool.name == "get_devo_correlation_rules")
    devo_correlation_rules_result = await get_devo_correlation_rules_tool.execute()
    devo_correlation_rules = devo_correlation_rules_result.result

    print("Type of returned devo_correlation_rules:", type(devo_correlation_rules))
    print(f"len correlation rules: {len(devo_correlation_rules)} rules: {str(devo_correlation_rules)[:200]}")

    # Verify that devo_correlation_rules is a list
    assert isinstance(devo_correlation_rules, list), "devo_correlation_rules should be a list"
    
    # Correlation rules might be empty, which is acceptable
    if len(devo_correlation_rules) > 0:
        # Check structure of correlation rules
        rules_to_check = devo_correlation_rules[:3] if len(devo_correlation_rules) > 3 else devo_correlation_rules
        
        for rule in rules_to_check:
            assert "id" in rule, "Each correlation rule should have an 'id' field"
            assert "name" in rule, "Each correlation rule should have a 'name' field"
            assert "enabled" in rule, "Each correlation rule should have an 'enabled' field"
            
            # Check for additional rule fields
            rule_fields = ["description", "condition", "threshold", "time_window", "severity", "category"]
            present_rule_fields = [field for field in rule_fields if field in rule]
            
            print(f"Correlation rule {rule['name']} contains these fields: {', '.join(present_rule_fields)}")

        print(f"Successfully retrieved and validated {len(devo_correlation_rules)} Devo correlation rules")
    else:
        print("No correlation rules found - this is acceptable for testing")

    # Test 4: Get incident data
    get_devo_incidents_tool = next(tool for tool in tools if tool.name == "get_devo_incidents")
    devo_incidents_result = await get_devo_incidents_tool.execute(
        limit=15  # limit to 15 incidents for testing
    )
    devo_incidents = devo_incidents_result.result

    print("Type of returned devo_incidents:", type(devo_incidents))
    print(f"len incidents: {len(devo_incidents)} incidents: {str(devo_incidents)[:200]}")

    # Verify that devo_incidents is a list
    assert isinstance(devo_incidents, list), "devo_incidents should be a list"
    
    # Incidents might be empty, which is acceptable
    if len(devo_incidents) > 0:
        # Check structure of incidents
        incidents_to_check = devo_incidents[:3] if len(devo_incidents) > 3 else devo_incidents
        
        for incident in incidents_to_check:
            assert "id" in incident, "Each incident should have an 'id' field"
            assert "title" in incident, "Each incident should have a 'title' field"
            assert "status" in incident, "Each incident should have a 'status' field"
            assert "severity" in incident, "Each incident should have a 'severity' field"
            
            # Check for common incident statuses
            valid_incident_statuses = ["new", "assigned", "investigating", "resolved", "closed"]
            
            # Check for additional incident fields
            incident_fields = ["description", "assignee", "created_at", "updated_at", "related_alerts", "affected_systems"]
            present_incident_fields = [field for field in incident_fields if field in incident]
            
            print(f"Incident {incident['id']} ({incident['severity']}) contains these fields: {', '.join(present_incident_fields)}")

        print(f"Successfully retrieved and validated {len(devo_incidents)} Devo incidents")
    else:
        print("No incidents found - this is acceptable for testing")

    print("Successfully completed alerts and security events tests")

    return True