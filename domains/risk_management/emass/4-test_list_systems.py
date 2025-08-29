# 4-test_list_systems.py

async def test_list_systems(zerg_state=None):
    """Test eMASS system enumeration by way of connector tools"""
    print("Testing eMASS system listing")

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

    # select systems to target
    system_selector = None
    for selector in emass_query_target_options.selectors:
        if selector.type == 'system_ids':  
            system_selector = selector
            break

    assert system_selector, "failed to retrieve system selector from query target options"

    # grab the first two systems 
    num_systems = 2
    assert isinstance(system_selector.values, list), "system_selector values must be a list"
    system_ids = system_selector.values[:num_systems] if system_selector.values else None
    print(f"Selecting system IDs: {system_ids}")

    assert system_ids, f"failed to retrieve {num_systems} system IDs from system selector"

    # set up the target with system IDs
    target = eMASSTarget(system_ids=system_ids)
    assert isinstance(target, ConnectorTargetInterface), "eMASSTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_emass_systems tool
    emass_get_systems_tool = next(tool for tool in tools if tool.name == "get_emass_systems")
    emass_systems_result = await emass_get_systems_tool.execute()
    emass_systems = emass_systems_result.result

    print("Type of returned emass_systems:", type(emass_systems))
    print(f"len systems: {len(emass_systems)} systems: {str(emass_systems)[:200]}")

    # Verify that emass_systems is a list
    assert isinstance(emass_systems, list), "emass_systems should be a list"
    assert len(emass_systems) > 0, "emass_systems should not be empty"
    assert len(emass_systems) == num_systems, f"emass_systems should have {num_systems} entries"
    
    # Verify structure of each system object
    for system in emass_systems:
        assert "systemId" in system, "Each system should have a 'systemId' field"
        assert system["systemId"] in system_ids, f"System ID {system['systemId']} is not in the requested system_ids"
        
        # Verify essential eMASS system fields
        assert "name" in system, "Each system should have a 'name' field"
        assert "acronym" in system, "Each system should have an 'acronym' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["description", "systemOwner", "authorizationStatus", "complianceLevel", "package"]
        present_fields = [field for field in descriptive_fields if field in system]
        
        print(f"System {system['systemId']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Verify authorization status is valid if present
        if "authorizationStatus" in system:
            valid_auth_statuses = ["ATO", "IATO", "P-ATO", "DENIED", "NOT_ASSESSED"]
            assert system["authorizationStatus"] in valid_auth_statuses, f"Authorization status should be valid"
        
        # Verify compliance level is valid if present
        if "complianceLevel" in system:
            valid_compliance_levels = ["FISMA_LOW", "FISMA_MODERATE", "FISMA_HIGH"]
            assert system["complianceLevel"] in valid_compliance_levels, f"Compliance level should be valid"
        
        # Check for package information if present
        if "package" in system:
            package_info = system["package"]
            assert isinstance(package_info, dict), "Package information should be a dictionary"
            
            # Check for package fields
            package_fields = ["id", "name", "type"]
            present_package_fields = [field for field in package_fields if field in package_info]
            print(f"Package contains these fields: {', '.join(present_package_fields)}")
        
        # Log the full structure of the first system
        if system == emass_systems[0]:
            print(f"Example system structure: {system}")

    print(f"Successfully retrieved and validated {len(emass_systems)} eMASS systems")

    return True