# 6-test_security_incidents.py

async def test_security_incidents(zerg_state=None):
    """Test Dragos security incident and event data retrieval by way of connector tools"""
    print("Attempting to authenticate using Dragos connector")

    assert zerg_state, "this test requires valid zerg_state"

    dragos_api_url = zerg_state.get("dragos_api_url").get("value")
    dragos_api_key = zerg_state.get("dragos_api_key").get("value")
    dragos_api_secret = zerg_state.get("dragos_api_secret").get("value")
    dragos_client_id = zerg_state.get("dragos_client_id").get("value")
    dragos_api_version = zerg_state.get("dragos_api_version").get("value")

    from connectors.dragos.config import DragosConnectorConfig
    from connectors.dragos.connector import DragosConnector
    from connectors.dragos.tools import DragosConnectorTools, GetSecurityIncidentsInput
    from connectors.dragos.target import DragosTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = DragosConnectorConfig(
        api_url=dragos_api_url,
        api_key=dragos_api_key,
        api_secret=dragos_api_secret,
        client_id=dragos_client_id,
        api_version=dragos_api_version
    )
    assert isinstance(config, ConnectorConfig), "DragosConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = DragosConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DragosConnector should be of type Connector"

    # get query target options
    dragos_query_target_options = await connector.get_query_target_options()
    assert isinstance(dragos_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select incident categories to target
    incident_category_selector = None
    for selector in dragos_query_target_options.selectors:
        if selector.type == 'incident_categories':  
            incident_category_selector = selector
            break

    incident_categories = None
    if incident_category_selector and isinstance(incident_category_selector.values, list) and incident_category_selector.values:
        incident_categories = incident_category_selector.values[:2]  # Select first 2 categories
        print(f"Selecting incident categories: {incident_categories}")

    # select monitoring scopes to target (optional)
    scope_selector = None
    for selector in dragos_query_target_options.selectors:
        if selector.type == 'monitoring_scopes':  
            scope_selector = selector
            break

    monitoring_scopes = None
    if scope_selector and isinstance(scope_selector.values, list) and scope_selector.values:
        monitoring_scopes = scope_selector.values[:1]  # Select first scope
        print(f"Selecting monitoring scopes: {monitoring_scopes}")

    # set up the target with incident categories and monitoring scopes
    target = DragosTarget(incident_categories=incident_categories, monitoring_scopes=monitoring_scopes)
    assert isinstance(target, ConnectorTargetInterface), "DragosTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_dragos_security_incidents tool and execute it
    get_security_incidents_tool = next(tool for tool in tools if tool.name == "get_dragos_security_incidents")
    
    # Get security incidents with detailed analysis
    security_incidents_result = await get_security_incidents_tool.execute(
        severity_filter="Medium", 
        include_analysis=True,
        include_recommendations=True,
        time_range="30days"
    )
    dragos_security_incidents = security_incidents_result.result

    print("Type of returned dragos_security_incidents:", type(dragos_security_incidents))
    print(f"len security incidents: {len(dragos_security_incidents)} incidents: {str(dragos_security_incidents)[:200]}")

    # Verify that dragos_security_incidents is a list
    assert isinstance(dragos_security_incidents, list), "dragos_security_incidents should be a list"
    assert len(dragos_security_incidents) > 0, "dragos_security_incidents should not be empty"
    
    # Limit the number of incidents to check if there are many
    incidents_to_check = dragos_security_incidents[:5] if len(dragos_security_incidents) > 5 else dragos_security_incidents
    
    # Verify structure of each security incident object
    for incident in incidents_to_check:
        # Verify essential Dragos security incident fields
        assert "incident_id" in incident, "Each incident should have an 'incident_id' field"
        assert "title" in incident, "Each incident should have a 'title' field"
        assert "severity" in incident, "Each incident should have a 'severity' field"
        
        # Verify severity is one of the expected values
        severity = incident["severity"]
        valid_severities = ["Low", "Medium", "High", "Critical", "Emergency"]
        assert severity in valid_severities, f"Incident severity {severity} should be one of {valid_severities}"
        
        # Verify common Dragos incident fields
        assert "timestamp" in incident, "Each incident should have a 'timestamp' field"
        assert "status" in incident, "Each incident should have a 'status' field"
        
        # Validate incident status
        status = incident["status"]
        valid_statuses = ["Open", "In_Progress", "Resolved", "Closed", "Under_Investigation"]
        assert status in valid_statuses, f"Incident status {status} should be one of {valid_statuses}"
        
        # Check for incident categorization and classification
        categorization_fields = ["incident_type", "category", "subcategory", "attack_vector"]
        present_categorization = [field for field in categorization_fields if field in incident]
        print(f"Incident {incident['incident_id']} contains these categorization fields: {', '.join(present_categorization)}")
        
        # Validate incident type if present
        if "incident_type" in incident:
            incident_type = incident["incident_type"]
            valid_types = ["Malware", "Unauthorized_Access", "Data_Breach", "DoS_Attack", "Protocol_Anomaly", "Asset_Compromise", "Safety_Event", "Unknown"]
            assert incident_type in valid_types, f"Incident type {incident_type} should be valid"
        
        # Check for affected assets and systems
        assert "affected_assets" in incident, "Each incident should have an 'affected_assets' field"
        affected_assets = incident["affected_assets"]
        assert isinstance(affected_assets, list), "Affected assets should be a list"
        
        if len(affected_assets) > 0:
            asset = affected_assets[0]  # Check first affected asset
            asset_fields = ["asset_id", "asset_name", "asset_type", "impact_level"]
            present_asset_fields = [field for field in asset_fields if field in asset]
            print(f"Affected asset contains: {', '.join(present_asset_fields)}")
            
            # Validate asset type for OT environments
            if "asset_type" in asset:
                asset_type = asset["asset_type"]
                valid_ot_types = ["PLC", "HMI", "SCADA", "DCS", "RTU", "Safety_System", "Network_Device"]
                if asset_type in valid_ot_types:
                    print(f"OT asset type validated: {asset_type}")
        
        # Check for threat intelligence and attribution
        threat_fields = ["threat_actors", "attack_campaign", "iocs", "threat_classification"]
        present_threat = [field for field in threat_fields if field in incident]
        print(f"Incident {incident['incident_id']} contains these threat fields: {', '.join(present_threat)}")
        
        # Validate IOCs structure if present
        if "iocs" in incident:
            iocs = incident["iocs"]
            assert isinstance(iocs, list), "IOCs should be a list"
            
            for ioc in iocs[:2]:  # Check first 2 IOCs
                ioc_fields = ["type", "value", "confidence", "source"]
                present_ioc_fields = [field for field in ioc_fields if field in ioc]
                print(f"IOC contains: {', '.join(present_ioc_fields)}")
        
        # Check for impact assessment and analysis
        impact_fields = ["impact_assessment", "business_impact", "safety_impact", "operational_impact"]
        present_impact = [field for field in impact_fields if field in incident]
        print(f"Incident {incident['incident_id']} contains these impact fields: {', '.join(present_impact)}")
        
        # Validate impact assessment if present
        if "impact_assessment" in incident:
            impact = incident["impact_assessment"]
            assert isinstance(impact, dict), "Impact assessment should be a dictionary"
            
            impact_metrics = ["severity_score", "affected_processes", "downtime_estimate", "recovery_time"]
            present_metrics = [field for field in impact_metrics if field in impact]
            print(f"Impact assessment contains: {', '.join(present_metrics)}")
        
        # Check for detection and response information
        detection_fields = ["detection_method", "detection_time", "response_actions", "containment_status"]
        present_detection = [field for field in detection_fields if field in incident]
        print(f"Incident {incident['incident_id']} contains these detection fields: {', '.join(present_detection)}")
        
        # Check for timeline and lifecycle tracking
        timeline_fields = ["first_detected", "escalation_time", "resolution_time", "timeline_events"]
        present_timeline = [field for field in timeline_fields if field in incident]
        print(f"Incident {incident['incident_id']} contains these timeline fields: {', '.join(present_timeline)}")
        
        # Validate timeline events if present
        if "timeline_events" in incident:
            timeline_events = incident["timeline_events"]
            assert isinstance(timeline_events, list), "Timeline events should be a list"
            
            for event in timeline_events[:2]:  # Check first 2 events
                event_fields = ["timestamp", "event_type", "description", "actor"]
                present_event_fields = [field for field in event_fields if field in event]
                print(f"Timeline event contains: {', '.join(present_event_fields)}")
        
        # Check for recommendations and remediation
        remediation_fields = ["recommendations", "remediation_steps", "preventive_measures", "lessons_learned"]
        present_remediation = [field for field in remediation_fields if field in incident]
        print(f"Incident {incident['incident_id']} contains these remediation fields: {', '.join(present_remediation)}")
        
        # Check for compliance and reporting context
        compliance_fields = ["regulatory_reporting", "compliance_violations", "notification_requirements"]
        present_compliance = [field for field in compliance_fields if field in incident]
        if present_compliance:
            print(f"Incident {incident['incident_id']} contains these compliance fields: {', '.join(present_compliance)}")
        
        # Verify incident category context if categories were selected
        if incident_categories:
            category_fields = ["incident_category", "category_classification", "sub_classification"]
            present_categories = [field for field in category_fields if field in incident]
            if present_categories:
                print(f"Incident {incident['incident_id']} contains these category fields: {', '.join(present_categories)}")
        
        # Check for investigation and forensics data
        forensics_fields = ["investigation_status", "evidence_collected", "forensic_analysis", "root_cause"]
        present_forensics = [field for field in forensics_fields if field in incident]
        print(f"Incident {incident['incident_id']} contains these forensics fields: {', '.join(present_forensics)}")
        
        # Check for communication and stakeholder management
        communication_fields = ["stakeholders_notified", "communication_log", "escalation_path", "external_contacts"]
        present_communication = [field for field in communication_fields if field in incident]
        print(f"Incident {incident['incident_id']} contains these communication fields: {', '.join(present_communication)}")
        
        # Log the structure of the first incident for debugging
        if incident == incidents_to_check[0]:
            print(f"Example security incident structure: {incident}")

    print(f"Successfully retrieved and validated {len(dragos_security_incidents)} Dragos security incidents")

    return True