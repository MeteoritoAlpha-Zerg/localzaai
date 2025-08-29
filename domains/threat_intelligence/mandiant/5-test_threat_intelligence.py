# 5-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Mandiant indicators and threat intelligence retrieval"""
    print("Attempting to retrieve threat intelligence using Mandiant connector")

    assert zerg_state, "this test requires valid zerg_state"

    mandiant_url = zerg_state.get("mandiant_url").get("value")
    mandiant_api_key = zerg_state.get("mandiant_api_key").get("value")
    mandiant_secret_key = zerg_state.get("mandiant_secret_key").get("value")

    from connectors.mandiant.config import MandiantConnectorConfig
    from connectors.mandiant.connector import MandiantConnector
    from connectors.mandiant.tools import MandiantConnectorTools
    from connectors.mandiant.target import MandiantTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = MandiantConnectorConfig(
        url=mandiant_url,
        api_key=mandiant_api_key,
        secret_key=mandiant_secret_key,
    )
    assert isinstance(config, ConnectorConfig), "MandiantConnectorConfig should be of type ConnectorConfig"

    connector = MandiantConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MandiantConnector should be of type Connector"

    mandiant_query_target_options = await connector.get_query_target_options()
    assert isinstance(mandiant_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    threat_actor_selector = None
    for selector in mandiant_query_target_options.selectors:
        if selector.type == 'threat_actor_ids':  
            threat_actor_selector = selector
            break

    assert threat_actor_selector, "failed to retrieve threat actor selector from query target options"

    assert isinstance(threat_actor_selector.values, list), "threat_actor_selector values must be a list"
    threat_actor_id = threat_actor_selector.values[0] if threat_actor_selector.values else None
    print(f"Selecting threat actor ID: {threat_actor_id}")

    assert threat_actor_id, f"failed to retrieve threat actor ID from threat actor selector"

    target = MandiantTarget(threat_actor_ids=[threat_actor_id])
    assert isinstance(target, ConnectorTargetInterface), "MandiantTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get indicators
    get_mandiant_indicators_tool = next(tool for tool in tools if tool.name == "get_mandiant_indicators")
    mandiant_indicators_result = await get_mandiant_indicators_tool.execute(
        threat_actor_id=threat_actor_id,
        limit=20
    )
    mandiant_indicators = mandiant_indicators_result.result

    print("Type of returned mandiant_indicators:", type(mandiant_indicators))
    print(f"len indicators: {len(mandiant_indicators)} indicators: {str(mandiant_indicators)[:200]}")

    assert isinstance(mandiant_indicators, list), "mandiant_indicators should be a list"
    
    if len(mandiant_indicators) > 0:
        indicators_to_check = mandiant_indicators[:5] if len(mandiant_indicators) > 5 else mandiant_indicators
        
        for indicator in indicators_to_check:
            assert "id" in indicator, "Each indicator should have an 'id' field"
            assert "type" in indicator, "Each indicator should have a 'type' field"
            assert "value" in indicator, "Each indicator should have a 'value' field"
            
            valid_indicator_types = ["ipv4", "fqdn", "url", "md5", "sha1", "sha256", "email", "registry_key"]
            assert indicator["type"] in valid_indicator_types, f"Indicator type {indicator['type']} is not valid"
            
            indicator_fields = ["confidence", "first_seen", "last_seen", "attribution", "categories", "threat_rating"]
            present_indicator_fields = [field for field in indicator_fields if field in indicator]
            
            print(f"Indicator {indicator['value']} ({indicator['type']}) contains these fields: {', '.join(present_indicator_fields)}")

        print(f"Successfully retrieved and validated {len(mandiant_indicators)} Mandiant indicators")

    # Test 2: Get threat reports
    get_mandiant_reports_tool = next(tool for tool in tools if tool.name == "get_mandiant_reports")
    mandiant_reports_result = await get_mandiant_reports_tool.execute(limit=10)
    mandiant_reports = mandiant_reports_result.result

    print("Type of returned mandiant_reports:", type(mandiant_reports))

    assert isinstance(mandiant_reports, list), "mandiant_reports should be a list"
    
    if len(mandiant_reports) > 0:
        reports_to_check = mandiant_reports[:3] if len(mandiant_reports) > 3 else mandiant_reports
        
        for report in reports_to_check:
            assert "id" in report, "Each report should have an 'id' field"
            assert "title" in report, "Each report should have a 'title' field"
            assert "report_type" in report, "Each report should have a 'report_type' field"
            
            valid_report_types = ["threat_actor", "malware", "campaign", "vulnerability", "threat_landscape"]
            
            report_fields = ["published_date", "executive_summary", "tags", "industries", "regions"]
            present_report_fields = [field for field in report_fields if field in report]
            
            print(f"Report {report['title']} ({report['report_type']}) contains these fields: {', '.join(present_report_fields)}")

        print(f"Successfully retrieved and validated {len(mandiant_reports)} Mandiant threat reports")

    # Test 3: Get vulnerabilities
    get_mandiant_vulnerabilities_tool = next(tool for tool in tools if tool.name == "get_mandiant_vulnerabilities")
    mandiant_vulnerabilities_result = await get_mandiant_vulnerabilities_tool.execute(limit=15)
    mandiant_vulnerabilities = mandiant_vulnerabilities_result.result

    print("Type of returned mandiant_vulnerabilities:", type(mandiant_vulnerabilities))

    assert isinstance(mandiant_vulnerabilities, list), "mandiant_vulnerabilities should be a list"
    
    if len(mandiant_vulnerabilities) > 0:
        vulns_to_check = mandiant_vulnerabilities[:3] if len(mandiant_vulnerabilities) > 3 else mandiant_vulnerabilities
        
        for vuln in vulns_to_check:
            assert "id" in vuln, "Each vulnerability should have an 'id' field"
            assert "cve_id" in vuln, "Each vulnerability should have a 'cve_id' field"
            assert "cvss_score" in vuln, "Each vulnerability should have a 'cvss_score' field"
            
            # Verify CVSS score is within valid range (0.0-10.0)
            assert 0.0 <= vuln["cvss_score"] <= 10.0, f"CVSS score {vuln['cvss_score']} is not within valid range"
            
            vuln_fields = ["title", "description", "exploit_available", "patch_available", "threat_actors"]
            present_vuln_fields = [field for field in vuln_fields if field in vuln]
            
            print(f"Vulnerability {vuln['cve_id']} (CVSS: {vuln['cvss_score']}) contains these fields: {', '.join(present_vuln_fields)}")

        print(f"Successfully retrieved and validated {len(mandiant_vulnerabilities)} Mandiant vulnerabilities")

    # Test 4: Get threat actor TTPs
    get_mandiant_ttps_tool = next(tool for tool in tools if tool.name == "get_mandiant_ttps")
    mandiant_ttps_result = await get_mandiant_ttps_tool.execute(threat_actor_id=threat_actor_id)
    mandiant_ttps = mandiant_ttps_result.result

    print("Type of returned mandiant_ttps:", type(mandiant_ttps))

    assert isinstance(mandiant_ttps, list), "mandiant_ttps should be a list"
    
    if len(mandiant_ttps) > 0:
        ttps_to_check = mandiant_ttps[:5] if len(mandiant_ttps) > 5 else mandiant_ttps
        
        for ttp in ttps_to_check:
            assert "technique_id" in ttp, "Each TTP should have a 'technique_id' field"
            assert "technique_name" in ttp, "Each TTP should have a 'technique_name' field"
            assert "tactic" in ttp, "Each TTP should have a 'tactic' field"
            
            # Verify MITRE ATT&CK technique ID format
            assert ttp["technique_id"].startswith("T"), f"Technique ID {ttp['technique_id']} should start with 'T'"
            
            ttp_fields = ["sub_technique", "description", "use_case", "platforms", "data_sources"]
            present_ttp_fields = [field for field in ttp_fields if field in ttp]
            
            print(f"TTP {ttp['technique_id']} ({ttp['technique_name']}) contains these fields: {', '.join(present_ttp_fields)}")

        print(f"Successfully retrieved and validated {len(mandiant_ttps)} Mandiant TTPs")

    print("Successfully completed threat intelligence and indicators tests")

    return True