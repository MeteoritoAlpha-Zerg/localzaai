# 5-test_asset_monitoring.py

async def test_asset_monitoring(zerg_state=None):
    """Test Dragos asset monitoring and vulnerability data retrieval by way of connector tools"""
    print("Attempting to authenticate using Dragos connector")

    assert zerg_state, "this test requires valid zerg_state"

    dragos_api_url = zerg_state.get("dragos_api_url").get("value")
    dragos_api_key = zerg_state.get("dragos_api_key").get("value")
    dragos_api_secret = zerg_state.get("dragos_api_secret").get("value")
    dragos_client_id = zerg_state.get("dragos_client_id").get("value")
    dragos_api_version = zerg_state.get("dragos_api_version").get("value")

    from connectors.dragos.config import DragosConnectorConfig
    from connectors.dragos.connector import DragosConnector
    from connectors.dragos.tools import DragosConnectorTools, GetAssetMonitoringInput
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

    # select asset monitoring targets
    asset_selector = None
    for selector in dragos_query_target_options.selectors:
        if selector.type == 'asset_groups':  
            asset_selector = selector
            break

    # Asset groups might be optional in some Dragos deployments
    asset_groups = None
    if asset_selector and isinstance(asset_selector.values, list) and asset_selector.values:
        asset_groups = asset_selector.values[:1]  # Select first asset group
        print(f"Selecting asset groups: {asset_groups}")

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

    # set up the target with asset groups and monitoring scopes
    target = DragosTarget(asset_groups=asset_groups, monitoring_scopes=monitoring_scopes)
    assert isinstance(target, ConnectorTargetInterface), "DragosTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_dragos_asset_monitoring tool and execute it
    get_asset_monitoring_tool = next(tool for tool in tools if tool.name == "get_dragos_asset_monitoring")
    
    # Get asset monitoring data with vulnerability analysis
    asset_monitoring_result = await get_asset_monitoring_tool.execute(
        include_vulnerabilities=True, 
        include_asset_details=True,
        severity_filter="Medium"
    )
    dragos_asset_monitoring = asset_monitoring_result.result

    print("Type of returned dragos_asset_monitoring:", type(dragos_asset_monitoring))
    print(f"len asset monitoring: {len(dragos_asset_monitoring)} assets: {str(dragos_asset_monitoring)[:200]}")

    # Verify that dragos_asset_monitoring is a list
    assert isinstance(dragos_asset_monitoring, list), "dragos_asset_monitoring should be a list"
    assert len(dragos_asset_monitoring) > 0, "dragos_asset_monitoring should not be empty"
    
    # Limit the number of assets to check if there are many
    assets_to_check = dragos_asset_monitoring[:5] if len(dragos_asset_monitoring) > 5 else dragos_asset_monitoring
    
    # Verify structure of each asset monitoring object
    for asset in assets_to_check:
        # Verify essential Dragos asset monitoring fields
        assert "asset_id" in asset, "Each asset should have an 'asset_id' field"
        assert "asset_name" in asset, "Each asset should have an 'asset_name' field"
        assert "asset_type" in asset, "Each asset should have an 'asset_type' field"
        
        # Verify asset type is appropriate for OT environments
        asset_type = asset["asset_type"]
        valid_ot_types = ["PLC", "HMI", "SCADA", "DCS", "RTU", "Safety_System", "Historian", "Engineering_Workstation", "Network_Device", "Unknown"]
        assert asset_type in valid_ot_types, f"Asset type {asset_type} should be valid OT asset type"
        
        # Check for network and identification information
        network_fields = ["ip_address", "mac_address", "network_segment", "vlan", "subnet"]
        present_network = [field for field in network_fields if field in asset]
        print(f"Asset {asset['asset_name']} contains these network fields: {', '.join(present_network)}")
        
        # Validate IP address format if present
        if "ip_address" in asset and asset["ip_address"]:
            ip_address = asset["ip_address"]
            assert isinstance(ip_address, str), "IP address should be a string"
            # Basic IP validation (IPv4 or IPv6)
            assert len(ip_address.split(".")) == 4 or ":" in ip_address, "IP should be IPv4 or IPv6 format"
        
        # Check for asset details and specifications
        detail_fields = ["vendor", "model", "firmware_version", "serial_number", "installation_date"]
        present_details = [field for field in detail_fields if field in asset]
        print(f"Asset {asset['asset_name']} contains these detail fields: {', '.join(present_details)}")
        
        # Check for operational status and monitoring
        status_fields = ["operational_status", "last_seen", "communication_status", "health_score"]
        present_status = [field for field in status_fields if field in asset]
        print(f"Asset {asset['asset_name']} contains these status fields: {', '.join(present_status)}")
        
        # Validate operational status if present
        if "operational_status" in asset:
            op_status = asset["operational_status"]
            valid_statuses = ["Online", "Offline", "Maintenance", "Error", "Unknown"]
            assert op_status in valid_statuses, f"Operational status {op_status} should be valid"
        
        # Check for vulnerability information
        vuln_fields = ["vulnerabilities", "cve_list", "risk_score", "patch_level"]
        present_vulns = [field for field in vuln_fields if field in asset]
        print(f"Asset {asset['asset_name']} contains these vulnerability fields: {', '.join(present_vulns)}")
        
        # Validate vulnerabilities structure if present
        if "vulnerabilities" in asset:
            vulnerabilities = asset["vulnerabilities"]
            assert isinstance(vulnerabilities, list), "Vulnerabilities should be a list"
            
            for vuln in vulnerabilities[:2]:  # Check first 2 vulnerabilities
                vuln_fields = ["cve_id", "severity", "description", "cvss_score", "exploit_available"]
                present_vuln_fields = [field for field in vuln_fields if field in vuln]
                print(f"Vulnerability contains: {', '.join(present_vuln_fields)}")
                
                # Validate CVE ID format if present
                if "cve_id" in vuln and vuln["cve_id"]:
                    cve_id = vuln["cve_id"]
                    assert cve_id.startswith("CVE-"), f"CVE ID should start with 'CVE-', got: {cve_id}"
                
                # Validate CVSS score if present
                if "cvss_score" in vuln and vuln["cvss_score"] is not None:
                    cvss_score = vuln["cvss_score"]
                    assert isinstance(cvss_score, (int, float)), "CVSS score should be numeric"
                    assert 0 <= cvss_score <= 10, f"CVSS score should be 0-10, got: {cvss_score}"
        
        # Check for security and compliance information
        security_fields = ["security_zone", "criticality_level", "compliance_status", "access_controls"]
        present_security = [field for field in security_fields if field in asset]
        print(f"Asset {asset['asset_name']} contains these security fields: {', '.join(present_security)}")
        
        # Validate criticality level if present
        if "criticality_level" in asset:
            criticality = asset["criticality_level"]
            valid_criticality = ["Low", "Medium", "High", "Critical", "Safety_Critical"]
            assert criticality in valid_criticality, f"Criticality {criticality} should be valid"
        
        # Check for protocol and communication information
        protocol_fields = ["protocols", "services", "communication_ports", "protocol_versions"]
        present_protocols = [field for field in protocol_fields if field in asset]
        print(f"Asset {asset['asset_name']} contains these protocol fields: {', '.join(present_protocols)}")
        
        # Check for monitoring and alerting configuration
        monitoring_fields = ["monitoring_enabled", "alert_thresholds", "baseline_behavior", "anomaly_detection"]
        present_monitoring = [field for field in monitoring_fields if field in asset]
        print(f"Asset {asset['asset_name']} contains these monitoring fields: {', '.join(present_monitoring)}")
        
        # Verify asset group context if groups were selected
        if asset_groups:
            group_fields = ["asset_group", "group_id", "group_classification"]
            present_groups = [field for field in group_fields if field in asset]
            if present_groups:
                print(f"Asset {asset['asset_name']} contains these group fields: {', '.join(present_groups)}")
        
        # Check for maintenance and lifecycle information
        lifecycle_fields = ["maintenance_schedule", "end_of_life", "support_status", "replacement_plan"]
        present_lifecycle = [field for field in lifecycle_fields if field in asset]
        print(f"Asset {asset['asset_name']} contains these lifecycle fields: {', '.join(present_lifecycle)}")
        
        # Log the structure of the first asset for debugging
        if asset == assets_to_check[0]:
            print(f"Example asset monitoring structure: {asset}")

    print(f"Successfully retrieved and validated {len(dragos_asset_monitoring)} Dragos asset monitoring records")

    return True