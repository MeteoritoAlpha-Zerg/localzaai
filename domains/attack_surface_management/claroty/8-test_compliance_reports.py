# 8-test_compliance_reports.py

async def test_compliance_reports(zerg_state=None):
    """Test Claroty compliance and governance reporting retrieval by way of connector tools"""
    print("Attempting to authenticate using Claroty connector")

    assert zerg_state, "this test requires valid zerg_state"

    claroty_server_url = zerg_state.get("claroty_server_url").get("value")
    claroty_api_token = zerg_state.get("claroty_api_token").get("value")
    claroty_username = zerg_state.get("claroty_username").get("value")
    claroty_password = zerg_state.get("claroty_password").get("value")
    claroty_api_version = zerg_state.get("claroty_api_version").get("value")

    from connectors.claroty.config import ClarotyConnectorConfig
    from connectors.claroty.connector import ClarotyConnector
    from connectors.claroty.tools import ClarotyConnectorTools, GetComplianceReportsInput
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

    # select security zones to target
    zone_selector = None
    for selector in claroty_query_target_options.selectors:
        if selector.type == 'security_zones':  
            zone_selector = selector
            break

    security_zones = None
    if zone_selector and isinstance(zone_selector.values, list) and zone_selector.values:
        # Select up to 2 security zones for compliance reporting
        security_zones = zone_selector.values[:2]
        print(f"Selecting security zones: {security_zones}")

    # select asset types to target (optional for compliance)
    asset_type_selector = None
    for selector in claroty_query_target_options.selectors:
        if selector.type == 'asset_types':  
            asset_type_selector = selector
            break

    asset_types = None
    if asset_type_selector and isinstance(asset_type_selector.values, list) and asset_type_selector.values:
        # Select first asset type for focused compliance analysis
        asset_types = asset_type_selector.values[:1]
        print(f"Selecting asset types: {asset_types}")

    # set up the target with security zones and asset types
    target = ClarotyTarget(security_zones=security_zones, asset_types=asset_types)
    assert isinstance(target, ConnectorTargetInterface), "ClarotyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_claroty_compliance_reports tool and execute it
    get_compliance_reports_tool = next(tool for tool in tools if tool.name == "get_claroty_compliance_reports")
    
    # Get compliance reports for major OT/ICS frameworks
    compliance_frameworks = ["NIST", "IEC62443", "NERC_CIP", "ISO27001"]
    compliance_result = await get_compliance_reports_tool.execute(
        frameworks=compliance_frameworks, 
        include_detailed_findings=True,
        report_period="quarterly"
    )
    claroty_compliance_reports = compliance_result.result

    print("Type of returned claroty_compliance_reports:", type(claroty_compliance_reports))
    print(f"compliance reports data: {str(claroty_compliance_reports)[:200]}")

    # Verify that claroty_compliance_reports is a dictionary
    assert isinstance(claroty_compliance_reports, dict), "claroty_compliance_reports should be a dictionary"
    assert len(claroty_compliance_reports) > 0, "claroty_compliance_reports should not be empty"
    
    # Verify essential compliance report structure
    assert "frameworks" in claroty_compliance_reports, "Compliance reports should have a 'frameworks' field"
    assert "summary" in claroty_compliance_reports, "Compliance reports should have a 'summary' field"
    
    frameworks_data = claroty_compliance_reports["frameworks"]
    summary_data = claroty_compliance_reports["summary"]
    
    assert isinstance(frameworks_data, dict), "Frameworks data should be a dictionary"
    assert isinstance(summary_data, dict), "Summary data should be a dictionary"
    assert len(frameworks_data) > 0, "Frameworks data should not be empty"
    
    print(f"Compliance report covers {len(frameworks_data)} frameworks")
    
    # Verify structure of each compliance framework report
    for framework_name, framework_data in frameworks_data.items():
        print(f"Analyzing compliance framework: {framework_name}")
        
        # Verify framework is one of the requested ones
        assert framework_name in compliance_frameworks, f"Framework {framework_name} should be in requested frameworks"
        
        # Verify essential framework report fields
        assert isinstance(framework_data, dict), f"Framework {framework_name} data should be a dictionary"
        assert "compliance_score" in framework_data, f"Framework {framework_name} should have a 'compliance_score' field"
        assert "status" in framework_data, f"Framework {framework_name} should have a 'status' field"
        
        # Verify compliance score is numeric and within valid range
        compliance_score = framework_data["compliance_score"]
        assert isinstance(compliance_score, (int, float)), f"Compliance score should be numeric, got: {type(compliance_score)}"
        assert 0 <= compliance_score <= 100, f"Compliance score should be between 0-100, got: {compliance_score}"
        
        # Verify compliance status
        valid_statuses = ["Compliant", "Partially Compliant", "Non-Compliant", "Under Review"]
        status = framework_data["status"]
        assert status in valid_statuses, f"Status {status} should be one of {valid_statuses}"
        
        # Check for control categories and requirements
        control_fields = ["controls", "requirements", "control_categories"]
        present_controls = [field for field in control_fields if field in framework_data]
        print(f"Framework {framework_name} contains these control fields: {', '.join(present_controls)}")
        
        # Validate controls structure if present
        if "controls" in framework_data:
            controls = framework_data["controls"]
            assert isinstance(controls, list), f"Controls for {framework_name} should be a list"
            
            if len(controls) > 0:
                # Check first few controls
                for control in controls[:3]:
                    control_fields = ["control_id", "title", "compliance_status", "implementation_level"]
                    present_control_fields = [field for field in control_fields if field in control]
                    print(f"Control contains: {', '.join(present_control_fields)}")
                    
                    # Verify control compliance status
                    if "compliance_status" in control:
                        control_status = control["compliance_status"]
                        valid_control_statuses = ["Implemented", "Partially Implemented", "Not Implemented", "Not Applicable"]
                        assert control_status in valid_control_statuses, f"Control status {control_status} should be valid"
        
        # Check for findings and gaps analysis
        findings_fields = ["findings", "gaps", "recommendations", "remediation_plan"]
        present_findings = [field for field in findings_fields if field in framework_data]
        print(f"Framework {framework_name} contains these findings fields: {', '.join(present_findings)}")
        
        # Validate findings structure if present
        if "findings" in framework_data:
            findings = framework_data["findings"]
            assert isinstance(findings, list), f"Findings for {framework_name} should be a list"
            
            for finding in findings[:2]:  # Check first 2 findings
                finding_fields = ["finding_id", "severity", "description", "affected_assets", "remediation_priority"]
                present_finding_fields = [field for field in finding_fields if field in finding]
                print(f"Finding contains: {', '.join(present_finding_fields)}")
                
                # Verify finding severity
                if "severity" in finding:
                    severity = finding["severity"]
                    valid_severities = ["Low", "Medium", "High", "Critical"]
                    assert severity in valid_severities, f"Finding severity {severity} should be valid"
        
        # Check for asset coverage and scope
        coverage_fields = ["asset_coverage", "scope", "assessment_date", "next_assessment"]
        present_coverage = [field for field in coverage_fields if field in framework_data]
        print(f"Framework {framework_name} contains these coverage fields: {', '.join(present_coverage)}")
        
        # Validate asset coverage if present
        if "asset_coverage" in framework_data:
            coverage = framework_data["asset_coverage"]
            assert isinstance(coverage, dict), "Asset coverage should be a dictionary"
            
            coverage_metrics = ["total_assets", "assessed_assets", "coverage_percentage"]
            present_metrics = [field for field in coverage_metrics if field in coverage]
            print(f"Asset coverage contains: {', '.join(present_metrics)}")
    
    # Verify compliance summary structure
    summary_fields = ["overall_compliance_score", "frameworks_count", "critical_findings", "improvement_trends"]
    present_summary = [field for field in summary_fields if field in summary_data]
    print(f"Compliance summary contains: {', '.join(present_summary)}")
    
    # Validate overall compliance score
    if "overall_compliance_score" in summary_data:
        overall_score = summary_data["overall_compliance_score"]
        assert isinstance(overall_score, (int, float)), "Overall compliance score should be numeric"
        assert 0 <= overall_score <= 100, f"Overall compliance score should be between 0-100, got: {overall_score}"
    
    # Check for regulatory and industry context
    regulatory_fields = ["regulatory_requirements", "industry_standards", "certification_status", "audit_trail"]
    present_regulatory = [field for field in regulatory_fields if field in claroty_compliance_reports]
    print(f"Compliance report contains these regulatory fields: {', '.join(present_regulatory)}")
    
    # Check for timeline and tracking information
    timeline_fields = ["report_generation_date", "assessment_period", "next_review_date", "compliance_trends"]
    present_timeline = [field for field in timeline_fields if field in claroty_compliance_reports]
    print(f"Compliance report contains these timeline fields: {', '.join(present_timeline)}")
    
    # Validate security zone and asset type context
    if security_zones:
        zone_fields = ["security_zones_assessed", "zone_compliance_breakdown"]
        present_zones = [field for field in zone_fields if field in claroty_compliance_reports]
        print(f"Compliance report contains these zone fields: {', '.join(present_zones)}")
    
    if asset_types:
        asset_fields = ["asset_types_assessed", "asset_compliance_breakdown"]
        present_assets = [field for field in asset_fields if field in claroty_compliance_reports]
        print(f"Compliance report contains these asset fields: {', '.join(present_assets)}")
    
    # Check for executive summary and reporting
    reporting_fields = ["executive_summary", "key_metrics", "action_items", "risk_assessment"]
    present_reporting = [field for field in reporting_fields if field in claroty_compliance_reports]
    print(f"Compliance report contains these reporting fields: {', '.join(present_reporting)}")
    
    # Log the overall structure for debugging
    print(f"Compliance report structure keys: {list(claroty_compliance_reports.keys())}")

    print(f"Successfully retrieved and validated Claroty compliance reports for {len(frameworks_data)} frameworks")

    return True