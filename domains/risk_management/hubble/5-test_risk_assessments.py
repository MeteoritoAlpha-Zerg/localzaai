# 5-test_risk_assessments.py

async def test_risk_assessments(zerg_state=None):
    """Test Hubble cybersecurity risk assessments and compliance data retrieval"""
    print("Attempting to retrieve risk assessments using Hubble connector")

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

    # Test 1: Get risk assessments
    get_hubble_risk_assessments_tool = next(tool for tool in tools if tool.name == "get_hubble_risk_assessments")
    hubble_risk_assessments_result = await get_hubble_risk_assessments_tool.execute(
        organization_id=organization_id,
        limit=20  # limit to 20 assessments for testing
    )
    hubble_risk_assessments = hubble_risk_assessments_result.result

    print("Type of returned hubble_risk_assessments:", type(hubble_risk_assessments))
    print(f"len risk assessments: {len(hubble_risk_assessments)} assessments: {str(hubble_risk_assessments)[:200]}")

    # Verify that hubble_risk_assessments is a list
    assert isinstance(hubble_risk_assessments, list), "hubble_risk_assessments should be a list"
    assert len(hubble_risk_assessments) > 0, "hubble_risk_assessments should not be empty"
    
    # Limit the number of assessments to check if there are many
    assessments_to_check = hubble_risk_assessments[:5] if len(hubble_risk_assessments) > 5 else hubble_risk_assessments
    
    # Verify structure of each risk assessment object
    for assessment in assessments_to_check:
        # Verify essential Hubble risk assessment fields
        assert "id" in assessment, "Each risk assessment should have an 'id' field"
        assert "organization_id" in assessment, "Each risk assessment should have an 'organization_id' field"
        assert "assessment_type" in assessment, "Each risk assessment should have an 'assessment_type' field"
        
        # Check that assessment belongs to the requested organization
        assert assessment["organization_id"] == organization_id, f"Assessment {assessment['id']} does not belong to the requested organization {organization_id}"
        
        # Verify common risk assessment fields
        assert "risk_score" in assessment, "Each risk assessment should have a 'risk_score' field"
        assert "completed_at" in assessment, "Each risk assessment should have a 'completed_at' field"
        assert "status" in assessment, "Each risk assessment should have a 'status' field"
        
        # Check for common assessment types
        valid_assessment_types = ["cybersecurity", "compliance", "vendor_risk", "third_party", "data_protection", "operational"]
        assert assessment["assessment_type"] in valid_assessment_types, f"Assessment type {assessment['assessment_type']} is not a recognized type"
        
        # Check for additional optional fields
        optional_fields = ["findings", "recommendations", "severity", "framework", "assessor", "next_assessment_date"]
        present_optional = [field for field in optional_fields if field in assessment]
        
        print(f"Risk assessment {assessment['id']} ({assessment['assessment_type']}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first assessment for debugging
        if assessment == assessments_to_check[0]:
            print(f"Example risk assessment structure: {assessment}")

    print(f"Successfully retrieved and validated {len(hubble_risk_assessments)} Hubble risk assessments")

    # Test 2: Get compliance data
    get_hubble_compliance_tool = next(tool for tool in tools if tool.name == "get_hubble_compliance")
    hubble_compliance_result = await get_hubble_compliance_tool.execute(
        organization_id=organization_id,
        limit=15  # limit to 15 compliance records for testing
    )
    hubble_compliance = hubble_compliance_result.result

    print("Type of returned hubble_compliance:", type(hubble_compliance))
    print(f"len compliance records: {len(hubble_compliance)} records: {str(hubble_compliance)[:200]}")

    # Verify that hubble_compliance is a list
    assert isinstance(hubble_compliance, list), "hubble_compliance should be a list"
    
    # Compliance data might be empty, which is acceptable
    if len(hubble_compliance) > 0:
        # Limit the number of compliance records to check
        compliance_to_check = hubble_compliance[:3] if len(hubble_compliance) > 3 else hubble_compliance
        
        # Verify structure of each compliance object
        for compliance in compliance_to_check:
            # Verify essential Hubble compliance fields
            assert "id" in compliance, "Each compliance record should have an 'id' field"
            assert "organization_id" in compliance, "Each compliance record should have an 'organization_id' field"
            assert "framework" in compliance, "Each compliance record should have a 'framework' field"
            
            # Check that compliance belongs to the requested organization
            assert compliance["organization_id"] == organization_id, f"Compliance {compliance['id']} does not belong to the requested organization {organization_id}"
            
            # Verify common compliance fields
            assert "compliance_status" in compliance, "Each compliance record should have a 'compliance_status' field"
            assert "last_assessed" in compliance, "Each compliance record should have a 'last_assessed' field"
            
            # Check for common compliance frameworks
            valid_frameworks = ["SOC2", "ISO27001", "NIST", "GDPR", "HIPAA", "PCI_DSS", "SOX", "FedRAMP"]
            assert compliance["framework"] in valid_frameworks, f"Framework {compliance['framework']} is not a recognized compliance framework"
            
            # Check for additional optional fields
            optional_fields = ["compliance_score", "gaps", "controls_implemented", "controls_total", "next_assessment"]
            present_optional = [field for field in optional_fields if field in compliance]
            
            print(f"Compliance {compliance['id']} ({compliance['framework']}) contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first compliance record for debugging
            if compliance == compliance_to_check[0]:
                print(f"Example compliance structure: {compliance}")

        print(f"Successfully retrieved and validated {len(hubble_compliance)} Hubble compliance records")
    else:
        print("No compliance records found - this is acceptable for testing")

    # Test 3: Get risk intelligence data
    get_hubble_risk_intelligence_tool = next(tool for tool in tools if tool.name == "get_hubble_risk_intelligence")
    hubble_risk_intelligence_result = await get_hubble_risk_intelligence_tool.execute(
        organization_id=organization_id,
        limit=10  # limit to 10 intelligence records for testing
    )
    hubble_risk_intelligence = hubble_risk_intelligence_result.result

    print("Type of returned hubble_risk_intelligence:", type(hubble_risk_intelligence))
    print(f"len risk intelligence records: {len(hubble_risk_intelligence)} records: {str(hubble_risk_intelligence)[:200]}")

    # Verify that hubble_risk_intelligence is a list
    assert isinstance(hubble_risk_intelligence, list), "hubble_risk_intelligence should be a list"
    
    # Risk intelligence might be empty, which is acceptable
    if len(hubble_risk_intelligence) > 0:
        # Check structure of risk intelligence records
        intelligence_to_check = hubble_risk_intelligence[:3] if len(hubble_risk_intelligence) > 3 else hubble_risk_intelligence
        
        for intelligence in intelligence_to_check:
            assert "id" in intelligence, "Each risk intelligence record should have an 'id' field"
            assert "risk_type" in intelligence, "Each risk intelligence record should have a 'risk_type' field"
            assert "severity" in intelligence, "Each risk intelligence record should have a 'severity' field"
            
            # Check for common risk types
            valid_risk_types = ["cyber_threat", "data_breach", "vendor_risk", "operational", "financial", "reputational", "regulatory"]
            assert intelligence["risk_type"] in valid_risk_types, f"Risk type {intelligence['risk_type']} is not a recognized type"
            
            print(f"Risk intelligence {intelligence['id']} for {intelligence['risk_type']} with severity {intelligence['severity']}")

        print(f"Successfully retrieved and validated {len(hubble_risk_intelligence)} Hubble risk intelligence records")
    else:
        print("No risk intelligence records found - this is acceptable for testing")

    print("Successfully completed risk assessments and compliance data tests")

    return True