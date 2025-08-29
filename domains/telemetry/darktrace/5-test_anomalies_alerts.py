# 5-test_anomalies_alerts.py

async def test_anomalies_alerts(zerg_state=None):
    """Test Darktrace security anomalies and alerts retrieval"""
    print("Attempting to retrieve anomalies and alerts using Darktrace connector")

    assert zerg_state, "this test requires valid zerg_state"

    darktrace_url = zerg_state.get("darktrace_url").get("value")
    darktrace_public_token = zerg_state.get("darktrace_public_token").get("value")
    darktrace_private_token = zerg_state.get("darktrace_private_token").get("value")

    from connectors.darktrace.config import DarktraceConnectorConfig
    from connectors.darktrace.connector import DarktraceConnector
    from connectors.darktrace.tools import DarktraceConnectorTools
    from connectors.darktrace.target import DarktraceTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = DarktraceConnectorConfig(
        url=darktrace_url,
        public_token=darktrace_public_token,
        private_token=darktrace_private_token,
    )
    assert isinstance(config, ConnectorConfig), "DarktraceConnectorConfig should be of type ConnectorConfig"

    connector = DarktraceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DarktraceConnector should be of type Connector"

    darktrace_query_target_options = await connector.get_query_target_options()
    assert isinstance(darktrace_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    model_selector = None
    for selector in darktrace_query_target_options.selectors:
        if selector.type == 'model_uuids':  
            model_selector = selector
            break

    assert model_selector, "failed to retrieve model selector from query target options"

    assert isinstance(model_selector.values, list), "model_selector values must be a list"
    model_uuid = model_selector.values[0] if model_selector.values else None
    print(f"Selecting model UUID: {model_uuid}")

    assert model_uuid, f"failed to retrieve model UUID from model selector"

    target = DarktraceTarget(model_uuids=[model_uuid])
    assert isinstance(target, ConnectorTargetInterface), "DarktraceTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get model breaches (anomalies)
    get_darktrace_breaches_tool = next(tool for tool in tools if tool.name == "get_darktrace_breaches")
    darktrace_breaches_result = await get_darktrace_breaches_tool.execute(
        model_uuid=model_uuid,
        limit=20
    )
    darktrace_breaches = darktrace_breaches_result.result

    print("Type of returned darktrace_breaches:", type(darktrace_breaches))
    print(f"len breaches: {len(darktrace_breaches)} breaches: {str(darktrace_breaches)[:200]}")

    assert isinstance(darktrace_breaches, list), "darktrace_breaches should be a list"
    
    if len(darktrace_breaches) > 0:
        breaches_to_check = darktrace_breaches[:3] if len(darktrace_breaches) > 3 else darktrace_breaches
        
        for breach in breaches_to_check:
            assert "pbid" in breach, "Each breach should have a 'pbid' field"
            assert "model" in breach, "Each breach should have a 'model' field"
            assert "time" in breach, "Each breach should have a 'time' field"
            assert "score" in breach, "Each breach should have a 'score' field"
            
            # Verify breach belongs to the requested model
            assert breach["model"]["uuid"] == model_uuid, f"Breach {breach['pbid']} does not belong to model {model_uuid}"
            
            breach_fields = ["device", "threatScore", "category", "commentCount", "acknowledged"]
            present_breach_fields = [field for field in breach_fields if field in breach]
            
            print(f"Breach {breach['pbid']} (score: {breach['score']}) contains these fields: {', '.join(present_breach_fields)}")

        print(f"Successfully retrieved and validated {len(darktrace_breaches)} Darktrace breaches")

    # Test 2: Get alerts
    get_darktrace_alerts_tool = next(tool for tool in tools if tool.name == "get_darktrace_alerts")
    darktrace_alerts_result = await get_darktrace_alerts_tool.execute(limit=15)
    darktrace_alerts = darktrace_alerts_result.result

    print("Type of returned darktrace_alerts:", type(darktrace_alerts))

    assert isinstance(darktrace_alerts, list), "darktrace_alerts should be a list"
    
    if len(darktrace_alerts) > 0:
        alerts_to_check = darktrace_alerts[:3] if len(darktrace_alerts) > 3 else darktrace_alerts
        
        for alert in alerts_to_check:
            assert "uuid" in alert, "Each alert should have a 'uuid' field"
            assert "title" in alert, "Each alert should have a 'title' field"
            assert "priority" in alert, "Each alert should have a 'priority' field"
            assert "creationTime" in alert, "Each alert should have a 'creationTime' field"
            
            valid_priorities = [1, 2, 3, 4, 5]  # Darktrace priority levels
            assert alert["priority"] in valid_priorities, f"Alert priority {alert['priority']} is not valid"
            
            alert_fields = ["category", "summary", "acknowledged", "currentGroup", "relatedBreaches"]
            present_alert_fields = [field for field in alert_fields if field in alert]
            
            print(f"Alert {alert['title']} (priority: {alert['priority']}) contains these fields: {', '.join(present_alert_fields)}")

        print(f"Successfully retrieved and validated {len(darktrace_alerts)} Darktrace alerts")

    # Test 3: Get AI Analyst incidents
    get_darktrace_incidents_tool = next(tool for tool in tools if tool.name == "get_darktrace_incidents")
    darktrace_incidents_result = await get_darktrace_incidents_tool.execute(limit=10)
    darktrace_incidents = darktrace_incidents_result.result

    print("Type of returned darktrace_incidents:", type(darktrace_incidents))

    assert isinstance(darktrace_incidents, list), "darktrace_incidents should be a list"
    
    if len(darktrace_incidents) > 0:
        incidents_to_check = darktrace_incidents[:3] if len(darktrace_incidents) > 3 else darktrace_incidents
        
        for incident in incidents_to_check:
            assert "id" in incident, "Each incident should have an 'id' field"
            assert "title" in incident, "Each incident should have a 'title' field"
            assert "score" in incident, "Each incident should have a 'score' field"
            
            incident_fields = ["summary", "groupCategory", "periods", "relatedBreaches", "aiAnalystScore"]
            present_incident_fields = [field for field in incident_fields if field in incident]
            
            print(f"AI Analyst incident {incident['title']} contains these fields: {', '.join(present_incident_fields)}")

        print(f"Successfully retrieved and validated {len(darktrace_incidents)} Darktrace AI Analyst incidents")

    print("Successfully completed anomalies and alerts tests")

    return True