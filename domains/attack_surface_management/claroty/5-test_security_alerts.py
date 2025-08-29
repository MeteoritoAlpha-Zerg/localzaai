# 5-test_security_alerts.py

async def test_security_alerts(zerg_state=None):
    """Test Claroty security alerts and threat detection retrieval by way of connector tools"""
    print("Attempting to authenticate using Claroty connector")

    assert zerg_state, "this test requires valid zerg_state"

    claroty_server_url = zerg_state.get("claroty_server_url").get("value")
    claroty_api_token = zerg_state.get("claroty_api_token").get("value")
    claroty_username = zerg_state.get("claroty_username").get("value")
    claroty_password = zerg_state.get("claroty_password").get("value")
    claroty_api_version = zerg_state.get("claroty_api_version").get("value")

    from connectors.claroty.config import ClarotyConnectorConfig
    from connectors.claroty.connector import ClarotyConnector
    from connectors.claroty.tools import ClarotyConnectorTools, GetSecurityAlertsInput
    from connectors.claroty.target import ClarotyTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ClarotyConnectorConfig(
        server_url=claroty_server_url,
        api_token=claroty_api_token,
        username=claroty_username,
        password=claroty_password,
        api_version=claroty_api_version
    )
    assert isinstance(config, ConnectorConfig), "ClarotyConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ClarotyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ClarotyConnector should be of type Connector"

    # get query target options
    claroty_query_target_options = await connector.get_query_target_options()
    assert isinstance(claroty_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select asset types to target
    asset_type_selector = None
    for selector in claroty_query_target_options.selectors:
        if selector.type == 'asset_types':  
            asset_type_selector = selector
            break

    assert asset_type_selector, "failed to retrieve asset type selector from query target options"

    assert isinstance(asset_type_selector.values, list), "asset_type_selector values must be a list"
    asset_type = asset_type_selector.values[0] if asset_type_selector.values else None
    print(f"Selecting asset type: {asset_type}")

    assert asset_type, f"failed to retrieve asset type from asset type selector"

    # select security zones to target (optional)
    zone_selector = None
    for selector in claroty_query_target_options.selectors:
        if selector.type == 'security_zones':  
            zone_selector = selector
            break

    security_zone = None
    if zone_selector and isinstance(zone_selector.values, list) and zone_selector.values:
        security_zone = zone_selector.values[0]
        print(f"Selecting security zone: {security_zone}")

    # set up the target with asset types and security zones
    target = ClarotyTarget(asset_types=[asset_type], security_zones=[security_zone] if security_zone else None)
    assert isinstance(target, ConnectorTargetInterface), "ClarotyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_claroty_security_alerts tool and execute it with severity filter
    get_security_alerts_tool = next(tool for tool in tools if tool.name == "get_claroty_security_alerts")
    
    # Filter for Medium severity and above alerts
    security_alerts_result = await get_security_alerts_tool.execute(severity_filter="Medium", limit=50)
    claroty_security_alerts = security_alerts_result.result

    print("Type of returned claroty_security_alerts:", type(claroty_security_alerts))
    print(f"len alerts: {len(claroty_security_alerts)} alerts: {str(claroty_security_alerts)[:200]}")

    # Verify that claroty_security_alerts is a list
    assert isinstance(claroty_security_alerts, list), "claroty_security_alerts should be a list"
    assert len(claroty_security_alerts) > 0, "claroty_security_alerts should not be empty"
    
    # Limit the number of alerts to check if there are many
    alerts_to_check = claroty_security_alerts[:5] if len(claroty_security_alerts) > 5 else claroty_security_alerts
    
    # Verify structure of each security alert object
    for alert in alerts_to_check:
        # Verify essential Claroty security alert fields
        assert "id" in alert, "Each alert should have an 'id' field"
        assert "title" in alert, "Each alert should have a 'title' field"
        assert "severity" in alert, "Each alert should have a 'severity' field"
        
        # Verify severity is one of the expected values
        valid_severities = ["Low", "Medium", "High", "Critical"]
        assert alert["severity"] in valid_severities, f"Alert severity {alert['severity']} should be one of {valid_severities}"
        
        # Verify common Claroty alert fields
        assert "timestamp" in alert, "Each alert should have a 'timestamp' field"
        assert "status" in alert, "Each alert should have a 'status' field"
        
        # Check for alert categorization and context
        categorization_fields = ["alert_type", "category", "subcategory", "threat_type"]
        present_categorization = [field for field in categorization_fields if field in alert]
        print(f"Alert {alert['id']} contains these categorization fields: {', '.join(present_categorization)}")
        
        # Check for affected assets and network context
        assert "affected_assets" in alert, "Each alert should have an 'affected_assets' field"
        affected_assets = alert["affected_assets"]
        assert isinstance(affected_assets, list), "Affected assets should be a list"
        
        if len(affected_assets) > 0:
            asset = affected_assets[0]  # Check first affected asset
            asset_fields = ["asset_id", "asset_name", "ip_address", "asset_type"]
            present_asset_fields = [field for field in asset_fields if field in asset]
            print(f"Affected asset contains: {', '.join(present_asset_fields)}")
        
        # Check for network and protocol information
        network_fields = ["source_ip", "destination_ip", "protocol", "port", "network_segment"]
        present_network = [field for field in network_fields if field in alert]
        print(f"Alert {alert['id']} contains these network fields: {', '.join(present_network)}")
        
        # Check for threat intelligence and detection details
        threat_fields = ["detection_method", "confidence_score", "threat_indicators", "mitre_tactics"]
        present_threat = [field for field in threat_fields if field in alert]
        print(f"Alert {alert['id']} contains these threat fields: {', '.join(present_threat)}")
        
        # Check for remediation and response information
        response_fields = ["description", "remediation_steps", "recommended_actions", "references"]
        present_response = [field for field in response_fields if field in alert]
        print(f"Alert {alert['id']} contains these response fields: {', '.join(present_response)}")
        
        # Verify security zone context if zones were selected
        if security_zone:
            zone_fields = ["security_zone", "zone_id", "network_segment"]
            present_zone = [field for field in zone_fields if field in alert]
            if present_zone:
                print(f"Alert {alert['id']} contains these zone fields: {', '.join(present_zone)}")
        
        # Check for compliance and regulatory context
        compliance_fields = ["compliance_frameworks", "regulatory_impact", "business_impact"]
        present_compliance = [field for field in compliance_fields if field in alert]
        if present_compliance:
            print(f"Alert {alert['id']} contains these compliance fields: {', '.join(present_compliance)}")
        
        # Log the structure of the first alert for debugging
        if alert == alerts_to_check[0]:
            print(f"Example alert structure: {alert}")

    print(f"Successfully retrieved and validated {len(claroty_security_alerts)} Claroty security alerts")

    return True