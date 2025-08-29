# 5-test_control_assessments.py

async def test_control_assessments(zerg_state=None):
    """Test eMASS security control assessment retrieval"""
    print("Testing eMASS security control assessment retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    emass_api_key = zerg_state.get("emass_api_key").get("value")
    emass_api_key_id = zerg_state.get("emass_api_key_id").get("value")
    emass_base_url = zerg_state.get("emass_base_url").get("value")
    emass_client_cert_path = zerg_state.get("emass_client_cert_path").get("value")
    emass_client_key_path = zerg_state.get("emass_client_key_path").get("value")

    from connectors.emass.config import eMASSConnectorConfig
    from connectors.emass.connector import eMASSConnector
    from connectors.emass.target import eMASSTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = eMASSConnectorConfig(
        api_key=emass_api_key,
        api_key_id=emass_api_key_id,
        base_url=emass_base_url,
        client_cert_path=emass_client_cert_path,
        client_key_path=emass_client_key_path
    )
    assert isinstance(config, ConnectorConfig), "eMASSConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = eMASSConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "eMASSConnector should be of type Connector"

    # get query target options
    emass_query_target_options = await connector.get_query_target_options()
    assert isinstance(emass_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select system to target
    system_selector = None
    for selector in emass_query_target_options.selectors:
        if selector.type == 'system_ids':  
            system_selector = selector
            break

    assert system_selector, "failed to retrieve system selector from query target options"

    assert isinstance(system_selector.values, list), "system_selector values must be a list"
    system_id = system_selector.values[0] if system_selector.values else None
    print(f"Selecting system ID: {system_id}")

    assert system_id, f"failed to retrieve system ID from system selector"

    # set up the target with system ID
    target = eMASSTarget(system_ids=[system_id])
    assert isinstance(target, ConnectorTargetInterface), "eMASSTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_control_assessments tool and execute it with system ID
    get_control_assessments_tool = next(tool for tool in tools if tool.name == "get_control_assessments")
    control_assessments_result = await get_control_assessments_tool.execute(system_id=system_id)
    control_assessments = control_assessments_result.result

    print("Type of returned control_assessments:", type(control_assessments))
    print(f"len assessments: {len(control_assessments)} assessments: {str(control_assessments)[:200]}")

    # Verify that control_assessments is a list
    assert isinstance(control_assessments, list), "control_assessments should be a list"
    assert len(control_assessments) > 0, "control_assessments should not be empty"
    
    # Limit the number of assessments to check if there are many
    assessments_to_check = control_assessments[:5] if len(control_assessments) > 5 else control_assessments
    
    # Verify structure of each control assessment object
    for assessment in assessments_to_check:
        # Verify assessment is a dictionary
        assert isinstance(assessment, dict), "Each control assessment should be a dictionary"
        
        # Verify essential control assessment fields
        assert "acronym" in assessment, "Each assessment should have an 'acronym' field"
        assert "implementationStatus" in assessment, "Each assessment should have an 'implementationStatus' field"
        
        # Verify control acronym format (should be NIST format like AC-1, AU-2, etc.)
        control_acronym = assessment["acronym"]
        assert isinstance(control_acronym, str), "Control acronym should be a string"
        assert "-" in control_acronym or control_acronym.upper() in ["COMMON", "HYBRID"], "Control acronym should be in NIST format or be COMMON/HYBRID"
        
        # Verify implementation status is valid
        valid_impl_statuses = ["Implemented", "Planned", "Alternative Implementation", "Not Applicable", "Not Assessed"]
        impl_status = assessment["implementationStatus"]
        assert impl_status in valid_impl_statuses, f"Implementation status {impl_status} should be valid"
        
        # Check for additional control assessment fields
        assessment_fields = ["title", "controlDesignation", "estimatedCompletionDate", "implementationGuidance", "assessmentProcedures"]
        present_assessment_fields = [field for field in assessment_fields if field in assessment]
        
        print(f"Control {control_acronym} contains these assessment fields: {', '.join(present_assessment_fields)}")
        
        # Verify control designation if present
        if "controlDesignation" in assessment:
            valid_designations = ["Common", "System-Specific", "Hybrid"]
            assert assessment["controlDesignation"] in valid_designations, f"Control designation should be valid"
        
        # Check for assessment procedures if present
        if "assessmentProcedures" in assessment:
            procedures = assessment["assessmentProcedures"]
            assert isinstance(procedures, (str, list)), "Assessment procedures should be string or list"
        
        # Check for estimated completion date if present
        if "estimatedCompletionDate" in assessment and assessment["estimatedCompletionDate"]:
            completion_date = assessment["estimatedCompletionDate"]
            assert isinstance(completion_date, (str, int)), "Completion date should be string or timestamp"
        
        # Log the structure of the first assessment for debugging
        if assessment == assessments_to_check[0]:
            print(f"Example control assessment structure: {assessment}")

    print(f"Successfully retrieved and validated {len(control_assessments)} control assessments")

    return True