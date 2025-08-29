# 5-test_get_issues.py

async def test_get_issues(zerg_state=None):
    """Test SecurityScorecard security issues retrieval"""
    print("Testing SecurityScorecard security issues retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    securityscorecard_api_url = zerg_state.get("securityscorecard_api_url").get("value")
    securityscorecard_api_token = zerg_state.get("securityscorecard_api_token").get("value")

    from connectors.securityscorecard.config import SecurityScorecardConnectorConfig
    from connectors.securityscorecard.connector import SecurityScorecardConnector
    from connectors.securityscorecard.target import SecurityScorecardTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = SecurityScorecardConnectorConfig(
        api_url=securityscorecard_api_url,
        api_token=securityscorecard_api_token
    )
    assert isinstance(config, ConnectorConfig), "SecurityScorecardConnectorConfig should be of type ConnectorConfig"

    connector = SecurityScorecardConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SecurityScorecardConnector should be of type Connector"

    securityscorecard_query_target_options = await connector.get_query_target_options()
    assert isinstance(securityscorecard_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in securityscorecard_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    issues_source = None
    for source in data_source_selector.values:
        if 'issue' in source.lower():
            issues_source = source
            break
    
    assert issues_source, "Issues data source not found in available options"
    print(f"Selecting issues data source: {issues_source}")

    target = SecurityScorecardTarget(data_sources=[issues_source])
    assert isinstance(target, ConnectorTargetInterface), "SecurityScorecardTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_securityscorecard_issues_tool = next(tool for tool in tools if tool.name == "get_securityscorecard_issues")
    issues_result = await get_securityscorecard_issues_tool.execute()
    issues_data = issues_result.result

    print("Type of returned issues data:", type(issues_data))
    print(f"Issues count: {len(issues_data)} sample: {str(issues_data)[:200]}")

    assert isinstance(issues_data, list), "Issues data should be a list"
    assert len(issues_data) > 0, "Issues data should not be empty"
    
    issues_to_check = issues_data[:10] if len(issues_data) > 10 else issues_data
    
    for issue in issues_to_check:
        # Verify essential issue fields per SecurityScorecard API specification
        assert "issue_type" in issue, "Each issue should have an 'issue_type' field"
        assert "severity" in issue, "Each issue should have a 'severity' field"
        assert "first_seen" in issue, "Each issue should have a 'first_seen' field"
        assert "factor" in issue, "Each issue should have a 'factor' field"
        
        assert issue["issue_type"].strip(), "Issue type should not be empty"
        assert issue["severity"].strip(), "Severity should not be empty"
        assert issue["first_seen"], "First seen should not be empty"
        assert issue["factor"].strip(), "Factor should not be empty"
        
        # Verify severity is valid
        valid_severities = ["low", "medium", "high", "critical"]
        severity = issue["severity"].lower()
        assert severity in valid_severities, f"Invalid severity level: {severity}"
        
        issue_fields = ["ip", "domain", "port", "last_seen", "details", "remediation_steps"]
        present_fields = [field for field in issue_fields if field in issue]
        
        print(f"Issue (type: {issue['issue_type']}, severity: {issue['severity']}, factor: {issue['factor']}) contains: {', '.join(present_fields)}")
        
        # If IP is present, validate it's not empty
        if "ip" in issue:
            ip = issue["ip"]
            assert ip and ip.strip(), "IP should not be empty"
        
        # If domain is present, validate it's not empty
        if "domain" in issue:
            domain = issue["domain"]
            assert domain and domain.strip(), "Domain should not be empty"
        
        # If port is present, validate it's within valid range
        if "port" in issue:
            port = issue["port"]
            if port is not None:
                assert isinstance(port, int), "Port should be an integer"
                assert 0 <= port <= 65535, f"Port should be between 0 and 65535: {port}"
        
        # If remediation steps are present, validate structure
        if "remediation_steps" in issue:
            remediation = issue["remediation_steps"]
            assert isinstance(remediation, list), "Remediation steps should be a list"
            for step in remediation:
                assert isinstance(step, str), "Each remediation step should be a string"
                assert step.strip(), "Remediation step should not be empty"
        
        # Log the structure of the first issue for debugging
        if issue == issues_to_check[0]:
            print(f"Example issue structure: {issue}")

    print(f"Successfully retrieved and validated {len(issues_data)} SecurityScorecard issues")

    return True