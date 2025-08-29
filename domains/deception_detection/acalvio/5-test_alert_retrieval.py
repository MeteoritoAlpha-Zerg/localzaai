# 5-test_alert_retrieval.py

async def test_alert_retrieval(zerg_state=None):
    """Test Acalvio security alert retrieval for selected environment"""
    print("Attempting to authenticate using Acalvio connector")

    assert zerg_state, "this test requires valid zerg_state"

    acalvio_api_url = zerg_state.get("acalvio_api_url").get("value")
    acalvio_api_key = zerg_state.get("acalvio_api_key").get("value")
    acalvio_username = zerg_state.get("acalvio_username").get("value")
    acalvio_password = zerg_state.get("acalvio_password").get("value")
    acalvio_tenant_id = zerg_state.get("acalvio_tenant_id").get("value")

    from connectors.acalvio.config import AcalvioConnectorConfig
    from connectors.acalvio.connector import AcalvioConnector
    from connectors.acalvio.tools import AcalvioConnectorTools, GetAcalvioAlertsInput
    from connectors.acalvio.target import AcalvioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = AcalvioConnectorConfig(
        api_url=acalvio_api_url,
        api_key=acalvio_api_key,
        username=acalvio_username,
        password=acalvio_password,
        tenant_id=acalvio_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "AcalvioConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = AcalvioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "AcalvioConnectorConfig should be of type ConnectorConfig"

    # get query target options
    acalvio_query_target_options = await connector.get_query_target_options()
    assert isinstance(acalvio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select environment to target
    environment_selector = None
    for selector in acalvio_query_target_options.selectors:
        if selector.type == 'environment_ids':  
            environment_selector = selector
            break

    assert environment_selector, "failed to retrieve environment selector from query target options"

    assert isinstance(environment_selector.values, list), "environment_selector values must be a list"
    environment_id = environment_selector.values[0] if environment_selector.values else None
    print(f"Selecting environment id: {environment_id}")

    assert environment_id, f"failed to retrieve environment id from environment selector"

    # set up the target with environment id
    target = AcalvioTarget(environment_ids=[environment_id])
    assert isinstance(target, ConnectorTargetInterface), "AcalvioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_acalvio_alerts tool and execute it with environment id
    get_acalvio_alerts_tool = next(tool for tool in tools if tool.name == "get_acalvio_alerts")
    acalvio_alerts_result = await get_acalvio_alerts_tool.execute(environment_id=environment_id)
    acalvio_alerts = acalvio_alerts_result.result

    print("Type of returned acalvio_alerts:", type(acalvio_alerts))
    print(f"len alerts: {len(acalvio_alerts)} alerts: {str(acalvio_alerts)[:200]}")

    # Verify that acalvio_alerts is a list
    assert isinstance(acalvio_alerts, list), "acalvio_alerts should be a list"
    assert len(acalvio_alerts) > 0, "acalvio_alerts should not be empty"
    
    # Limit the number of alerts to check if there are many
    alerts_to_check = acalvio_alerts[:5] if len(acalvio_alerts) > 5 else acalvio_alerts
    
    # Verify structure of each alert object
    for alert in alerts_to_check:
        # Verify essential Acalvio alert fields
        assert "id" in alert, "Each alert should have an 'id' field"
        assert "environment_id" in alert, "Each alert should have an 'environment_id' field"
        assert "timestamp" in alert, "Each alert should have a 'timestamp' field"
        assert "severity" in alert, "Each alert should have a 'severity' field"
        assert "alert_type" in alert, "Each alert should have an 'alert_type' field"
        
        # Check if alert belongs to the requested environment
        assert alert["environment_id"] == environment_id, f"Alert {alert['id']} does not belong to the requested environment_id"
        
        # Verify common Acalvio alert fields
        assert "title" in alert, "Each alert should have a 'title' field"
        assert "description" in alert, "Each alert should have a 'description' field"
        assert "status" in alert, "Each alert should have a 'status' field"
        
        # Verify severity levels
        valid_severities = ["low", "medium", "high", "critical"]
        assert alert["severity"].lower() in valid_severities, f"Alert severity should be one of {valid_severities}"
        
        # Check for additional optional fields
        optional_fields = ["source_ip", "destination_ip", "asset_name", "attack_vector", "mitre_techniques", "threat_score", "response_actions"]
        present_optional = [field for field in optional_fields if field in alert]
        
        print(f"Alert {alert['id']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first alert for debugging
        if alert == alerts_to_check[0]:
            print(f"Example alert structure: {alert}")

    print(f"Successfully retrieved and validated {len(acalvio_alerts)} Acalvio security alerts")

    return True