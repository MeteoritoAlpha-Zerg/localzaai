# 6-test_security_posture.py

async def test_security_posture(zerg_state=None):
    """Test Hubble security posture assessments and vulnerability data retrieval"""
    print("Attempting to retrieve security posture data using Hubble connector")

    assert zerg_state, "this test requires valid zerg_state"

    hubble_url = zerg_state.get("hubble_url").get("value")
    hubble_api_key = zerg_state.get("hubble_api_key", {}).get("value")
    hubble_client_id = zerg_state.get("hubble_client_id", {}).get("value")
    hubble_client_secret = zerg_state.get("hubble_client_secret", {}).get("value")

    from connectors.hubble.config import HubbleConnectorConfig
    from connectors.hubble.connector import HubbleConnector
    from connectors.hubble.tools import HubbleConnectorTools
    from connectors.hubble.target import HubbleTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config - prefer API key over OAuth
    if hubble_api_key:
        config = HubbleConnectorConfig(
            url=hubble_url,
            api_key=hubble_api_key,
        )
    elif hubble_client_id and hubble_client_secret:
        config = HubbleConnectorConfig(
            url=hubble_url,
            client_id=hubble_client_id,
            client_secret=hubble_client_secret,
        )
    else:
        raise Exception("Either hubble_api_key or both hubble_client_id and hubble_client_secret must be provided")

    assert isinstance(config, ConnectorConfig), "HubbleConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = HubbleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "HubbleConnector should be of type Connector"

    # get query target options
    hubble_query_target_options = await connector.get_query_target_options()
    assert isinstance(hubble_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select organizations to target
    organization_selector = None
    for selector in hubble_query_target_options.selectors:
        if selector.type == 'organization_ids':  
            organization_selector = selector
            break

    assert organization_selector, "failed to retrieve organization selector from query target options"

    assert isinstance(organization_selector.values, list), "organization_selector values must be a list"
    organization_id = organization_selector.values[0] if organization_selector.values else None
    print(f"Selecting organization ID: {organization_id}")

    assert organization_id, f"failed to retrieve organization ID from organization selector"

    # set up the target with organization IDs
    target = HubbleTarget(organization_ids=[organization_id])
    assert isinstance(target, ConnectorTargetInterface), "HubbleTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get security posture assessments
    get_hubble_security_posture_tool = next(tool for tool in tools if tool.name == "get_hubble_security_posture")
    hubble_security_posture_result = await get_hubble_security_posture_tool.execute(
        organization_id=organization_id,
        limit=15  # limit to 15 posture assessments for testing
    )
    hubble_security_posture = hubble_security_posture_result.result

    print("Type of returned hubble_security_posture:", type(hubble_security_posture))
    print(f"len security posture assessments: {len(hubble_security_posture)} assessments: {str(hubble_security_posture)[:200]}")

    # Verify that hubble_security_posture is a list
    assert isinstance(hubble_security_posture, list), "hubble_security_posture should be a list"
    
    # Security posture might be empty, which is acceptable
    if len(hubble_security_posture) > 0:
        # Limit the number of posture assessments to check if there are many
        posture_to_check = hubble_security_posture[:5] if len(hubble_security_posture) > 5 else hubble_security_posture
        
        # Verify structure of each security posture object
        for posture in posture_to_check:
            # Verify essential Hubble security posture fields
            assert "id" in posture, "Each security posture should have an 'id' field"
            assert "organization_id" in posture, "Each security posture should have an 'organization_id' field"
            assert "posture_score" in posture, "Each security posture should have a 'posture_score' field"
            
            # Check that posture belongs to the requested organization
            assert posture["organization_id"] == organization_id, f"Security posture {posture['id']} does not belong to the requested organization {organization_id}"
            
            # Verify common security posture fields
            assert "assessment_date" in posture, "Each security posture should have an 'assessment_date' field"
            assert "category" in posture, "Each security posture should have a 'category' field"
            
            # Check for common posture categories
            valid_categories = ["network_security", "endpoint_security", "data_protection", "access_management", "incident_response", "governance"]
            assert posture["category"] in valid_categories, f"Posture category {posture['category']} is not a recognized category"
            
            # Check for additional optional fields
            optional_fields = ["strengths", "weaknesses", "recommendations", "trend", "benchmark", "maturity_level"]
            present_optional = [field for field in optional_fields if field in posture]
            
            print(f"Security posture {posture['id']} ({posture['category']}) contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first posture assessment for debugging
            if posture == posture_to_check[0]:
                print(f"Example security posture structure: {posture}")

        print(f"Successfully retrieved and validated {len(hubble_security_posture)} Hubble security posture assessments")
    else:
        print("No security posture assessments found - this is acceptable for testing")

    # Test 2: Get vulnerability assessments
    get_hubble_vulnerabilities_tool = next(tool for tool in tools if tool.name == "get_hubble_vulnerabilities")
    hubble_vulnerabilities_result = await get_hubble_vulnerabilities_tool.execute(
        organization_id=organization_id,
        limit=25  # limit to 25 vulnerabilities for testing
    )
    hubble_vulnerabilities = hubble_vulnerabilities_result.result

    print("Type of returned hubble_vulnerabilities:", type(hubble_vulnerabilities))
    print(f"len vulnerabilities: {len(hubble_vulnerabilities)} vulnerabilities: {str(hubble_vulnerabilities)[:200]}")

    # Verify that hubble_vulnerabilities is a list
    assert isinstance(hubble_vulnerabilities, list), "hubble_vulnerabilities should be a list"
    
    # Vulnerabilities might be empty, which is acceptable
    if len(hubble_vulnerabilities) > 0:
        # Limit the number of vulnerabilities to check
        vulnerabilities_to_check = hubble_vulnerabilities[:5] if len(hubble_vulnerabilities) > 5 else hubble_vulnerabilities
        
        # Verify structure of each vulnerability object
        for vulnerability in vulnerabilities_to_check:
            # Verify essential Hubble vulnerability fields
            assert "id" in vulnerability, "Each vulnerability should have an 'id' field"
            assert "organization_id" in vulnerability, "Each vulnerability should have an 'organization_id' field"
            assert "severity" in vulnerability, "Each vulnerability should have a 'severity' field"
            
            # Check that vulnerability belongs to the requested organization
            assert vulnerability["organization_id"] == organization_id, f"Vulnerability {vulnerability['id']} does not belong to the requested organization {organization_id}"
            
            # Verify common vulnerability fields
            assert "title" in vulnerability, "Each vulnerability should have a 'title' field"
            assert "discovered_date" in vulnerability, "Each vulnerability should have a 'discovered_date' field"
            assert "status" in vulnerability, "Each vulnerability should have a 'status' field"
            
            # Check for common severity levels
            valid_severities = ["critical", "high", "medium", "low", "informational"]
            assert vulnerability["severity"] in valid_severities, f"Vulnerability severity {vulnerability['severity']} is not a recognized severity"
            
            # Check for common vulnerability statuses
            valid_statuses = ["open", "in_progress", "resolved", "accepted_risk", "false_positive"]
            assert vulnerability["status"] in valid_statuses, f"Vulnerability status {vulnerability['status']} is not a recognized status"
            
            # Check for additional optional fields
            optional_fields = ["cve_id", "cvss_score", "asset", "remediation", "exploitability", "patch_available"]
            present_optional = [field for field in optional_fields if field in vulnerability]
            
            print(f"Vulnerability {vulnerability['id']} ({vulnerability['severity']}) contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first vulnerability for debugging
            if vulnerability == vulnerabilities_to_check[0]:
                print(f"Example vulnerability structure: {vulnerability}")

        print(f"Successfully retrieved and validated {len(hubble_vulnerabilities)} Hubble vulnerabilities")
    else:
        print("No vulnerabilities found - this is acceptable for testing")

    # Test 3: Get security metrics
    get_hubble_security_metrics_tool = next(tool for tool in tools if tool.name == "get_hubble_security_metrics")
    hubble_security_metrics_result = await get_hubble_security_metrics_tool.execute(
        organization_id=organization_id
    )
    hubble_security_metrics = hubble_security_metrics_result.result

    print("Type of returned hubble_security_metrics:", type(hubble_security_metrics))
    print(f"Security metrics: {str(hubble_security_metrics)[:200]}")

    # Verify that hubble_security_metrics is a dictionary
    assert isinstance(hubble_security_metrics, dict), "hubble_security_metrics should be a dictionary"
    
    # Security metrics might be empty, which is acceptable
    if hubble_security_metrics:
        # Check for common security metrics
        expected_metrics = ["overall_risk_score", "vulnerability_count", "compliance_percentage", "incident_count", "security_maturity"]
        present_metrics = [metric for metric in expected_metrics if metric in hubble_security_metrics]
        
        print(f"Security metrics contains these fields: {', '.join(present_metrics)}")
        
        # Verify organization ID matches
        if "organization_id" in hubble_security_metrics:
            assert hubble_security_metrics["organization_id"] == organization_id, "Security metrics organization_id should match requested organization"

        print(f"Successfully retrieved Hubble security metrics for organization {organization_id}")
    else:
        print("No security metrics found - this is acceptable for testing")

    # Test 4: Get threat landscape data
    get_hubble_threat_landscape_tool = next(tool for tool in tools if tool.name == "get_hubble_threat_landscape")
    hubble_threat_landscape_result = await get_hubble_threat_landscape_tool.execute(
        organization_id=organization_id,
        limit=10  # limit to 10 threat landscape records for testing
    )
    hubble_threat_landscape = hubble_threat_landscape_result.result

    print("Type of returned hubble_threat_landscape:", type(hubble_threat_landscape))
    print(f"len threat landscape records: {len(hubble_threat_landscape)} records: {str(hubble_threat_landscape)[:200]}")

    # Verify that hubble_threat_landscape is a list
    assert isinstance(hubble_threat_landscape, list), "hubble_threat_landscape should be a list"
    
    # Threat landscape might be empty, which is acceptable
    if len(hubble_threat_landscape) > 0:
        # Check structure of threat landscape records
        landscape_to_check = hubble_threat_landscape[:3] if len(hubble_threat_landscape) > 3 else hubble_threat_landscape
        
        for landscape in landscape_to_check:
            assert "threat_type" in landscape, "Each threat landscape record should have a 'threat_type' field"
            assert "probability" in landscape, "Each threat landscape record should have a 'probability' field"
            assert "impact" in landscape, "Each threat landscape record should have an 'impact' field"
            
            # Check for common threat types
            valid_threat_types = ["ransomware", "phishing", "data_breach", "insider_threat", "supply_chain", "ddos", "malware"]
            assert landscape["threat_type"] in valid_threat_types, f"Threat type {landscape['threat_type']} is not a recognized type"
            
            print(f"Threat landscape for {landscape['threat_type']} with probability {landscape['probability']} and impact {landscape['impact']}")

        print(f"Successfully retrieved and validated {len(hubble_threat_landscape)} Hubble threat landscape records")
    else:
        print("No threat landscape records found - this is acceptable for testing")

    print("Successfully completed security posture and vulnerability assessment tests")

    return True