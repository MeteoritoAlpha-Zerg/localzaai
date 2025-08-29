# 5-test_finding_details.py

async def test_finding_details(zerg_state=None):
    """Test retrieving detailed information for a specific GuardDuty finding ID"""
    print("Attempting to authenticate using GuardDuty connector")

    assert zerg_state, "this test requires valid zerg_state"

    aws_region = zerg_state.get("aws_region").get("value")
    aws_access_key_id = zerg_state.get("aws_access_key_id").get("value")
    aws_secret_access_key = zerg_state.get("aws_secret_access_key").get("value")
    aws_session_token = zerg_state.get("aws_session_token").get("value")

    from connectors.guardduty.config import GuardDutyConnectorConfig
    from connectors.guardduty.connector import GuardDutyConnector
    from connectors.guardduty.tools import GuardDutyConnectorTools
    from connectors.guardduty.target import GuardDutyTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = GuardDutyConnectorConfig(
        region=aws_region,
        access_key_id=aws_access_key_id,
        secret_access_key=aws_secret_access_key,
        session_token=aws_session_token
    )
    assert isinstance(config, ConnectorConfig), "GuardDutyConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = GuardDutyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GuardDutyConnector should be of type Connector"

    # get query target options
    guardduty_query_target_options = await connector.get_query_target_options()
    assert isinstance(guardduty_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select detectors to target
    detector_selector = None
    for selector in guardduty_query_target_options.selectors:
        if selector.type == 'detectors':  
            detector_selector = selector
            break

    assert detector_selector, "failed to retrieve detector selector from query target options"

    assert isinstance(detector_selector.values, list), "detector_selector values must be a list"
    detector_id = detector_selector.values[0] if detector_selector.values else None
    print(f"Selecting detector ID: {detector_id}")

    assert detector_id, f"failed to retrieve detector ID from detector selector"

    # set up the target with detector IDs
    target = GuardDutyTarget(detectors=[detector_id])
    assert isinstance(target, ConnectorTargetInterface), "GuardDutyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # First get a list of findings to select one for detailed inspection
    get_guardduty_findings_tool = next(tool for tool in tools if tool.name == "get_guardduty_findings")
    guardduty_findings_result = await get_guardduty_findings_tool.execute(detector_id=detector_id)
    guardduty_findings = guardduty_findings_result.raw_result

    # Verify that findings exist to test with
    assert isinstance(guardduty_findings, list), "guardduty_findings should be a list"
    assert len(guardduty_findings) > 0, "No GuardDuty findings available for testing finding details"
    
    # Select a finding ID to retrieve details for
    finding_id = guardduty_findings[0]["id"]
    print(f"Selected finding ID for detailed inspection: {finding_id}")
    
    # Get the finding details tool
    get_finding_details_tool = next(tool for tool in tools if tool.name == "get_finding_details")
    finding_details_result = await get_finding_details_tool.execute(
        detector_id=detector_id,
        finding_id=finding_id
    )
    finding_details = finding_details_result.raw_result
    
    print("Type of returned finding_details:", type(finding_details))
    print(f"Finding details: {str(finding_details)[:200]}...")
    
    # Verify that finding_details is a dictionary
    assert isinstance(finding_details, dict), "finding_details should be a dictionary"
    
    # Verify essential GuardDuty finding details fields
    assert "id" in finding_details, "Finding details should have an 'id' field"
    assert finding_details["id"] == finding_id, "Finding ID in details should match requested ID"
    assert "detectorId" in finding_details, "Finding details should have a 'detectorId' field"
    assert finding_details["detectorId"] == detector_id, "Detector ID in details should match requested detector"
    
    # Check for critical finding information fields
    essential_fields = [
        "title", "description", "severity", "type", "updatedAt", "createdAt", "arn"
    ]
    for field in essential_fields:
        assert field in finding_details, f"Finding details should contain '{field}'"
    
    # Check for detailed information fields
    detailed_fields = [
        "resource", "service"
    ]
    for field in detailed_fields:
        assert field in finding_details, f"Finding details should contain detailed '{field}' information"
    
    # Check for resource information if present
    resource_info = finding_details.get("resource", {})
    if resource_info:
        assert isinstance(resource_info, dict), "Resource information should be a dictionary"
        print(f"Resource information fields: {', '.join(resource_info.keys())}")
        
        # Check for common resource fields
        resource_fields = ["resourceType", "instanceDetails", "s3BucketDetails", "accessKeyDetails"]
        present_resource_fields = [field for field in resource_fields if field in resource_info]
        print(f"Present resource fields: {', '.join(present_resource_fields)}")
        
        assert len(present_resource_fields) > 0, "Resource information should contain at least one detail field"
    
    # Check for service information if present
    service_info = finding_details.get("service", {})
    if service_info:
        assert isinstance(service_info, dict), "Service information should be a dictionary"
        print(f"Service information fields: {', '.join(service_info.keys())}")
        
        # Check for common service fields
        service_fields = ["serviceName", "detectorId", "action", "resourceRole", "count"]
        present_service_fields = [field for field in service_fields if field in service_info]
        print(f"Present service fields: {', '.join(present_service_fields)}")
        
        assert len(present_service_fields) > 0, "Service information should contain at least one detail field"
    
    # Check for remediation recommendations if present
    if "service" in finding_details and "additionalInfo" in finding_details["service"]:
        additional_info = finding_details["service"]["additionalInfo"]
        if "recommendation" in additional_info:
            recommendation = additional_info["recommendation"]
            print(f"Remediation recommendation: {recommendation}")
    
    print(f"Successfully retrieved and validated detailed information for GuardDuty finding {finding_id}")
    
    return True