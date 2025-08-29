# 6-test_risk_management.py

async def test_risk_management(zerg_state=None):
    """Test eMASS risk management reports and POA&M data analysis"""
    print("Testing eMASS risk management reports and POA&M data analysis")

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

    # get query target options to find available systems
    emass_query_target_options = await connector.get_query_target_options()
    assert isinstance(emass_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select system to target for risk management analysis
    system_selector = None
    for selector in emass_query_target_options.selectors:
        if selector.type == 'system_ids':  
            system_selector = selector
            break

    assert system_selector, "failed to retrieve system selector from query target options"

    assert isinstance(system_selector.values, list), "system_selector values must be a list"
    system_id = system_selector.values[0] if system_selector.values else None
    print(f"Using system for risk management analysis: {system_id}")

    assert system_id, f"failed to retrieve system ID from system selector"

    # set up the target with system ID
    target = eMASSTarget(system_ids=[system_id])
    assert isinstance(target, ConnectorTargetInterface), "eMASSTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_risk_management tool and execute risk management analysis
    get_risk_mgmt_tool = next(tool for tool in tools if tool.name == "get_risk_management")
    
    # Execute risk management analysis
    risk_mgmt_result = await get_risk_mgmt_tool.execute(system_id=system_id)
    risk_management = risk_mgmt_result.result

    print("Type of returned risk_management:", type(risk_management))
    print(f"Risk management preview: {str(risk_management)[:200]}")

    # Verify that risk_management contains structured data
    assert risk_management is not None, "risk_management should not be None"
    
    # Risk management could be a dictionary with metrics or a list of POA&M items
    if isinstance(risk_management, dict):
        # Check for common risk management fields
        expected_fields = ["totalPoams", "openPoams", "closedPoams", "riskScore", "complianceScore", "poamItems"]
        present_fields = [field for field in expected_fields if field in risk_management]
        
        assert len(present_fields) > 0, f"Risk management should contain at least one of these fields: {expected_fields}"
        print(f"Risk management contains these fields: {', '.join(present_fields)}")
        
        # Verify numeric fields are actually numeric
        for field in present_fields:
            if "total" in field.lower() or "score" in field.lower() or "poams" in field.lower():
                assert isinstance(risk_management[field], (int, float)), f"Field {field} should be numeric"
        
        # Check for POA&M items if present
        if "poamItems" in risk_management:
            poam_items = risk_management["poamItems"]
            assert isinstance(poam_items, list), "poamItems should be a list"
            
            if len(poam_items) > 0:
                sample_poam = poam_items[0]
                poam_fields = ["poamId", "status", "vulnerability", "scheduledCompletionDate", "riskLevel"]
                present_poam_fields = [field for field in poam_fields if field in sample_poam]
                print(f"POA&M items contain these fields: {', '.join(present_poam_fields)}")
                
                # Verify POA&M status if present
                if "status" in sample_poam:
                    valid_poam_statuses = ["Ongoing", "Risk Accepted", "Completed", "Not Applicable"]
                    assert sample_poam["status"] in valid_poam_statuses, f"POA&M status should be valid"
        
        # Log the full structure for debugging
        print(f"Risk management structure: {risk_management}")
        
    elif isinstance(risk_management, list):
        assert len(risk_management) > 0, "Risk management list should not be empty"
        
        # Check structure of risk management items (likely POA&Ms)
        sample_item = risk_management[0]
        assert isinstance(sample_item, dict), "Risk management items should be dictionaries"
        
        # Look for common POA&M fields
        item_fields = ["poamId", "vulnerabilityDescription", "status", "riskLevel", "scheduledCompletionDate"]
        present_item_fields = [field for field in item_fields if field in sample_item]
        
        print(f"Risk management items contain these fields: {', '.join(present_item_fields)}")
        
        # Verify POA&M ID if present
        if "poamId" in sample_item:
            poam_id = sample_item["poamId"]
            assert isinstance(poam_id, (str, int)), "POA&M ID should be string or integer"
        
        # Verify risk level if present
        if "riskLevel" in sample_item:
            valid_risk_levels = ["Very Low", "Low", "Moderate", "High", "Very High"]
            assert sample_item["riskLevel"] in valid_risk_levels, f"Risk level should be valid"
        
        # Check for vulnerability description if present
        if "vulnerabilityDescription" in sample_item:
            vuln_desc = sample_item["vulnerabilityDescription"]
            assert isinstance(vuln_desc, str), "Vulnerability description should be a string"
            assert len(vuln_desc.strip()) > 0, "Vulnerability description should not be empty"
        
        # Check for scheduled completion date if present
        if "scheduledCompletionDate" in sample_item and sample_item["scheduledCompletionDate"]:
            completion_date = sample_item["scheduledCompletionDate"]
            assert isinstance(completion_date, (str, int)), "Completion date should be string or timestamp"
        
        print(f"Example risk management item: {sample_item}")
        
    else:
        # Risk management could be in other formats, ensure it's meaningful
        assert str(risk_management).strip() != "", "Risk management should contain meaningful data"

    print(f"Successfully retrieved and validated risk management data")

    return True