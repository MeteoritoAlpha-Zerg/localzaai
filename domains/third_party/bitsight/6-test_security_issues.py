# 6-test_security_issues.py

async def test_security_issues(zerg_state=None):
    """Test BitSight security issues and findings retrieval"""
    print("Attempting to retrieve security issues using BitSight connector")

    assert zerg_state, "this test requires valid zerg_state"

    bitsight_url = zerg_state.get("bitsight_url").get("value")
    bitsight_api_token = zerg_state.get("bitsight_api_token").get("value")

    from connectors.bitsight.config import BitSightConnectorConfig
    from connectors.bitsight.connector import BitSightConnector
    from connectors.bitsight.tools import BitSightConnectorTools
    from connectors.bitsight.target import BitSightTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = BitSightConnectorConfig(
        url=bitsight_url,
        api_token=bitsight_api_token,
    )
    assert isinstance(config, ConnectorConfig), "BitSightConnectorConfig should be of type ConnectorConfig"

    connector = BitSightConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "BitSightConnector should be of type Connector"

    bitsight_query_target_options = await connector.get_query_target_options()
    assert isinstance(bitsight_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    company_selector = None
    for selector in bitsight_query_target_options.selectors:
        if selector.type == 'company_guids':  
            company_selector = selector
            break

    assert company_selector, "failed to retrieve company selector from query target options"

    assert isinstance(company_selector.values, list), "company_selector values must be a list"
    company_guid = company_selector.values[0] if company_selector.values else None
    print(f"Selecting company GUID: {company_guid}")

    assert company_guid, f"failed to retrieve company GUID from company selector"

    target = BitSightTarget(company_guids=[company_guid])
    assert isinstance(target, ConnectorTargetInterface), "BitSightTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get security findings
    get_bitsight_findings_tool = next(tool for tool in tools if tool.name == "get_bitsight_findings")
    bitsight_findings_result = await get_bitsight_findings_tool.execute(
        company_guid=company_guid,
        limit=20
    )
    bitsight_findings = bitsight_findings_result.result

    print("Type of returned bitsight_findings:", type(bitsight_findings))
    print(f"len findings: {len(bitsight_findings)} findings: {str(bitsight_findings)[:200]}")

    assert isinstance(bitsight_findings, list), "bitsight_findings should be a list"
    
    if len(bitsight_findings) > 0:
        findings_to_check = bitsight_findings[:5] if len(bitsight_findings) > 5 else bitsight_findings
        
        for finding in findings_to_check:
            assert "risk_vector" in finding, "Each finding should have a 'risk_vector' field"
            assert "risk_category" in finding, "Each finding should have a 'risk_category' field"
            assert "severity" in finding, "Each finding should have a 'severity' field"
            assert "first_seen" in finding, "Each finding should have a 'first_seen' field"
            
            # Verify severity is valid
            valid_severities = ["WARN", "MATERIAL", "MINOR"]
            assert finding["severity"] in valid_severities, f"Finding severity {finding['severity']} is not valid"
            
            finding_fields = ["last_seen", "details", "assets", "evidence_key", "confidence"]
            present_finding_fields = [field for field in finding_fields if field in finding]
            
            print(f"Finding in {finding['risk_vector']} ({finding['severity']}) contains these fields: {', '.join(present_finding_fields)}")

        print(f"Successfully retrieved and validated {len(bitsight_findings)} BitSight findings")

    # Test 2: Get vulnerabilities
    get_bitsight_vulnerabilities_tool = next(tool for tool in tools if tool.name == "get_bitsight_vulnerabilities")
    bitsight_vulnerabilities_result = await get_bitsight_vulnerabilities_tool.execute(
        company_guid=company_guid,
        limit=15
    )
    bitsight_vulnerabilities = bitsight_vulnerabilities_result.result

    print("Type of returned bitsight_vulnerabilities:", type(bitsight_vulnerabilities))

    assert isinstance(bitsight_vulnerabilities, list), "bitsight_vulnerabilities should be a list"
    
    if len(bitsight_vulnerabilities) > 0:
        vulns_to_check = bitsight_vulnerabilities[:3] if len(bitsight_vulnerabilities) > 3 else bitsight_vulnerabilities
        
        for vuln in vulns_to_check:
            assert "vulnerability_id" in vuln, "Each vulnerability should have a 'vulnerability_id' field"
            assert "severity" in vuln, "Each vulnerability should have a 'severity' field"
            assert "cvss_score" in vuln, "Each vulnerability should have a 'cvss_score' field"
            
            # Verify CVSS score is within valid range (0.0-10.0)
            assert 0.0 <= vuln["cvss_score"] <= 10.0, f"CVSS score {vuln['cvss_score']} is not within valid range"
            
            vuln_fields = ["cve_id", "description", "port", "service", "first_seen", "last_seen"]
            present_vuln_fields = [field for field in vuln_fields if field in vuln]
            
            print(f"Vulnerability {vuln['vulnerability_id']} (CVSS: {vuln['cvss_score']}) contains these fields: {', '.join(present_vuln_fields)}")

        print(f"Successfully retrieved and validated {len(bitsight_vulnerabilities)} BitSight vulnerabilities")

    # Test 3: Get alerts
    get_bitsight_alerts_tool = next(tool for tool in tools if tool.name == "get_bitsight_alerts")
    bitsight_alerts_result = await get_bitsight_alerts_tool.execute(company_guid=company_guid)
    bitsight_alerts = bitsight_alerts_result.result

    print("Type of returned bitsight_alerts:", type(bitsight_alerts))

    assert isinstance(bitsight_alerts, list), "bitsight_alerts should be a list"
    
    if len(bitsight_alerts) > 0:
        alerts_to_check = bitsight_alerts[:3] if len(bitsight_alerts) > 3 else bitsight_alerts
        
        for alert in alerts_to_check:
            assert "alert_uuid" in alert, "Each alert should have an 'alert_uuid' field"
            assert "alert_date" in alert, "Each alert should have an 'alert_date' field"
            assert "trigger" in alert, "Each alert should have a 'trigger' field"
            
            alert_fields = ["risk_category", "summary", "details", "companies_affected"]
            present_alert_fields = [field for field in alert_fields if field in alert]
            
            print(f"Alert {alert['alert_uuid']} contains these fields: {', '.join(present_alert_fields)}")

        print(f"Successfully retrieved and validated {len(bitsight_alerts)} BitSight alerts")

    # Test 4: Get breach data
    get_bitsight_breaches_tool = next(tool for tool in tools if tool.name == "get_bitsight_breaches")
    bitsight_breaches_result = await get_bitsight_breaches_tool.execute(company_guid=company_guid)
    bitsight_breaches = bitsight_breaches_result.result

    print("Type of returned bitsight_breaches:", type(bitsight_breaches))

    assert isinstance(bitsight_breaches, list), "bitsight_breaches should be a list"
    
    if len(bitsight_breaches) > 0:
        breaches_to_check = bitsight_breaches[:3] if len(bitsight_breaches) > 3 else bitsight_breaches
        
        for breach in breaches_to_check:
            assert "breach_id" in breach, "Each breach should have a 'breach_id' field"
            assert "breach_date" in breach, "Each breach should have a 'breach_date' field"
            assert "records_lost" in breach, "Each breach should have a 'records_lost' field"
            
            breach_fields = ["breach_type", "industry", "description", "source"]
            present_breach_fields = [field for field in breach_fields if field in breach]
            
            print(f"Breach {breach['breach_id']} contains these fields: {', '.join(present_breach_fields)}")

        print(f"Successfully retrieved and validated {len(bitsight_breaches)} BitSight breaches")

    # Test 5: Get security diligence
    get_bitsight_diligence_tool = next(tool for tool in tools if tool.name == "get_bitsight_diligence")
    bitsight_diligence_result = await get_bitsight_diligence_tool.execute(company_guid=company_guid)
    bitsight_diligence = bitsight_diligence_result.result

    print("Type of returned bitsight_diligence:", type(bitsight_diligence))

    assert isinstance(bitsight_diligence, dict), "bitsight_diligence should be a dictionary"
    
    if bitsight_diligence:
        diligence_fields = ["security_practices", "incident_response", "data_governance", "vendor_management"]
        present_diligence_fields = [field for field in diligence_fields if field in bitsight_diligence]
        
        print(f"Security diligence contains these fields: {', '.join(present_diligence_fields)}")

    print("Successfully completed security issues and findings tests")

    return True