# 6-test_security_issues.py

async def test_security_issues(zerg_state=None):
    """Test UpGuard security issues and vulnerabilities retrieval"""
    print("Attempting to retrieve security issues using UpGuard connector")

    assert zerg_state, "this test requires valid zerg_state"

    upguard_url = zerg_state.get("upguard_url").get("value")
    upguard_api_key = zerg_state.get("upguard_api_key").get("value")

    from connectors.upguard.config import UpGuardConnectorConfig
    from connectors.upguard.connector import UpGuardConnector
    from connectors.upguard.tools import UpGuardConnectorTools
    from connectors.upguard.target import UpGuardTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = UpGuardConnectorConfig(
        url=upguard_url,
        api_key=upguard_api_key,
    )
    assert isinstance(config, ConnectorConfig), "UpGuardConnectorConfig should be of type ConnectorConfig"

    connector = UpGuardConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "UpGuardConnector should be of type Connector"

    upguard_query_target_options = await connector.get_query_target_options()
    assert isinstance(upguard_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    vendor_selector = None
    for selector in upguard_query_target_options.selectors:
        if selector.type == 'vendor_ids':  
            vendor_selector = selector
            break

    assert vendor_selector, "failed to retrieve vendor selector from query target options"

    assert isinstance(vendor_selector.values, list), "vendor_selector values must be a list"
    vendor_id = vendor_selector.values[0] if vendor_selector.values else None
    print(f"Selecting vendor ID: {vendor_id}")

    assert vendor_id, f"failed to retrieve vendor ID from vendor selector"

    target = UpGuardTarget(vendor_ids=[vendor_id])
    assert isinstance(target, ConnectorTargetInterface), "UpGuardTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get security risks
    get_upguard_risks_tool = next(tool for tool in tools if tool.name == "get_upguard_risks")
    upguard_risks_result = await get_upguard_risks_tool.execute(
        vendor_id=vendor_id,
        limit=20
    )
    upguard_risks = upguard_risks_result.result

    print("Type of returned upguard_risks:", type(upguard_risks))
    print(f"len risks: {len(upguard_risks)} risks: {str(upguard_risks)[:200]}")

    assert isinstance(upguard_risks, list), "upguard_risks should be a list"
    
    if len(upguard_risks) > 0:
        risks_to_check = upguard_risks[:5] if len(upguard_risks) > 5 else upguard_risks
        
        for risk in risks_to_check:
            assert "id" in risk, "Each risk should have an 'id' field"
            assert "title" in risk, "Each risk should have a 'title' field"
            assert "severity" in risk, "Each risk should have a 'severity' field"
            assert "category" in risk, "Each risk should have a 'category' field"
            
            valid_severities = ["high", "medium", "low", "info"]
            assert risk["severity"] in valid_severities, f"Risk severity {risk['severity']} is not valid"
            
            risk_fields = ["description", "hostname", "ip", "port", "first_seen", "last_seen", "status"]
            present_risk_fields = [field for field in risk_fields if field in risk]
            
            print(f"Risk {risk['title']} ({risk['severity']}) contains these fields: {', '.join(present_risk_fields)}")

        print(f"Successfully retrieved and validated {len(upguard_risks)} UpGuard risks")

    # Test 2: Get vulnerabilities
    get_upguard_vulnerabilities_tool = next(tool for tool in tools if tool.name == "get_upguard_vulnerabilities")
    upguard_vulnerabilities_result = await get_upguard_vulnerabilities_tool.execute(
        vendor_id=vendor_id,
        limit=15
    )
    upguard_vulnerabilities = upguard_vulnerabilities_result.result

    print("Type of returned upguard_vulnerabilities:", type(upguard_vulnerabilities))

    assert isinstance(upguard_vulnerabilities, list), "upguard_vulnerabilities should be a list"
    
    if len(upguard_vulnerabilities) > 0:
        vulns_to_check = upguard_vulnerabilities[:3] if len(upguard_vulnerabilities) > 3 else upguard_vulnerabilities
        
        for vuln in vulns_to_check:
            assert "id" in vuln, "Each vulnerability should have an 'id' field"
            assert "title" in vuln, "Each vulnerability should have a 'title' field"
            assert "severity" in vuln, "Each vulnerability should have a 'severity' field"
            
            vuln_fields = ["cve_id", "cvss_score", "description", "solution", "hostname", "port"]
            present_vuln_fields = [field for field in vuln_fields if field in vuln]
            
            print(f"Vulnerability {vuln['title']} ({vuln['severity']}) contains these fields: {', '.join(present_vuln_fields)}")

        print(f"Successfully retrieved and validated {len(upguard_vulnerabilities)} UpGuard vulnerabilities")

    # Test 3: Get data breaches
    get_upguard_breaches_tool = next(tool for tool in tools if tool.name == "get_upguard_breaches")
    upguard_breaches_result = await get_upguard_breaches_tool.execute(vendor_id=vendor_id)
    upguard_breaches = upguard_breaches_result.result

    print("Type of returned upguard_breaches:", type(upguard_breaches))

    assert isinstance(upguard_breaches, list), "upguard_breaches should be a list"
    
    if len(upguard_breaches) > 0:
        breaches_to_check = upguard_breaches[:3] if len(upguard_breaches) > 3 else upguard_breaches
        
        for breach in breaches_to_check:
            assert "id" in breach, "Each breach should have an 'id' field"
            assert "date" in breach, "Each breach should have a 'date' field"
            assert "records_lost" in breach, "Each breach should have a 'records_lost' field"
            
            breach_fields = ["breach_type", "description", "source", "confidence"]
            present_breach_fields = [field for field in breach_fields if field in breach]
            
            print(f"Breach {breach['id']} contains these fields: {', '.join(present_breach_fields)}")

        print(f"Successfully retrieved and validated {len(upguard_breaches)} UpGuard breaches")

    # Test 4: Get typosquatting domains
    get_upguard_typosquatting_tool = next(tool for tool in tools if tool.name == "get_upguard_typosquatting")
    upguard_typosquatting_result = await get_upguard_typosquatting_tool.execute(vendor_id=vendor_id)
    upguard_typosquatting = upguard_typosquatting_result.result

    print("Type of returned upguard_typosquatting:", type(upguard_typosquatting))

    assert isinstance(upguard_typosquatting, list), "upguard_typosquatting should be a list"
    
    if len(upguard_typosquatting) > 0:
        typo_to_check = upguard_typosquatting[:3] if len(upguard_typosquatting) > 3 else upguard_typosquatting
        
        for typo in typo_to_check:
            assert "domain" in typo, "Each typosquatting entry should have a 'domain' field"
            assert "risk_level" in typo, "Each typosquatting entry should have a 'risk_level' field"
            
            typo_fields = ["registered_date", "registrar", "ip_address", "malicious"]
            present_typo_fields = [field for field in typo_fields if field in typo]
            
            print(f"Typosquatting domain {typo['domain']} contains these fields: {', '.join(present_typo_fields)}")

        print(f"Successfully retrieved and validated {len(upguard_typosquatting)} UpGuard typosquatting domains")

    # Test 5: Get dark web mentions
    get_upguard_dark_web_tool = next(tool for tool in tools if tool.name == "get_upguard_dark_web")
    upguard_dark_web_result = await get_upguard_dark_web_tool.execute(vendor_id=vendor_id)
    upguard_dark_web = upguard_dark_web_result.result

    print("Type of returned upguard_dark_web:", type(upguard_dark_web))

    assert isinstance(upguard_dark_web, list), "upguard_dark_web should be a list"
    
    if len(upguard_dark_web) > 0:
        dark_web_to_check = upguard_dark_web[:3] if len(upguard_dark_web) > 3 else upguard_dark_web
        
        for mention in dark_web_to_check:
            assert "id" in mention, "Each dark web mention should have an 'id' field"
            assert "source" in mention, "Each dark web mention should have a 'source' field"
            assert "date" in mention, "Each dark web mention should have a 'date' field"
            
            mention_fields = ["title", "content", "url", "risk_level", "category"]
            present_mention_fields = [field for field in mention_fields if field in mention]
            
            print(f"Dark web mention from {mention['source']} contains these fields: {', '.join(present_mention_fields)}")

        print(f"Successfully retrieved and validated {len(upguard_dark_web)} UpGuard dark web mentions")

    print("Successfully completed security issues and vulnerabilities tests")

    return True