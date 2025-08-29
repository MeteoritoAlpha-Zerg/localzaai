# 4-test_list_findings.py

# 4-test_list_findings.py

async def test_list_findings(zerg_state=None):
    """Test listing GuardDuty findings for selected detectors in target"""
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

    # grab the get_guardduty_findings tool and execute it with detector_id
    get_guardduty_findings_tool = next(tool for tool in tools if tool.name == "get_guardduty_findings")
    guardduty_findings_result = await get_guardduty_findings_tool.execute(detector_id=detector_id)
    guardduty_findings = guardduty_findings_result.raw_result

    print("Type of returned guardduty_findings:", type(guardduty_findings))
    print(f"len findings: {len(guardduty_findings)} findings: {str(guardduty_findings)[:200]}")

    # Verify that guardduty_findings is a list
    assert isinstance(guardduty_findings, list), "guardduty_findings should be a list"
    
    # If findings exist, verify their structure
    if len(guardduty_findings) > 0:
        # Limit the number of findings to check if there are many
        findings_to_check = guardduty_findings[:5] if len(guardduty_findings) > 5 else guardduty_findings
        
        # Verify structure of each finding object
        for finding in findings_to_check:
            # Verify essential GuardDuty finding fields
            assert "id" in finding, "Each finding should have an 'id' field"
            assert "arn" in finding, "Each finding should have an 'arn' field"
            assert "type" in finding, "Each finding should have a 'type' field"
            
            # Check if finding belongs to the specified detector
            assert "detectorId" in finding, "Each finding should have a 'detectorId' field"
            assert finding["detectorId"] == detector_id, f"Finding {finding['id']} does not belong to the requested detector"
            
            # Verify common GuardDuty finding fields
            essential_fields = ["title", "description", "severity", "updatedAt", "createdAt"]
            for field in essential_fields:
                assert field in finding, f"Finding should contain '{field}'"
            
            # Additional optional fields to check (if present)
            optional_fields = ["accountId", "region", "resource", "service", "partition"]
            present_optional = [field for field in optional_fields if field in finding]
            
            print(f"Finding {finding['id']} contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first finding for debugging
            if finding == findings_to_check[0]:
                print(f"Example finding structure: {finding}")

        print(f"Successfully retrieved and validated {len(guardduty_findings)} GuardDuty findings")
    else:
        print("No GuardDuty findings found for the selected detector. This is acceptable for the test.")

    return True