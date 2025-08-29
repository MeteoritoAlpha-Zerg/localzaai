# 5-test_ioc_retrieval.py

async def test_ioc_retrieval(zerg_state=None):
    """Test MISP IOC retrieval from events"""
    print("Attempting to retrieve IOCs using MISP connector")

    assert zerg_state, "this test requires valid zerg_state"

    misp_url = zerg_state.get("misp_url").get("value")
    misp_api_key = zerg_state.get("misp_api_key").get("value")

    from connectors.misp.config import MISPConnectorConfig
    from connectors.misp.connector import MISPConnector
    from connectors.misp.tools import MISPConnectorTools, GetMISPIOCsInput
    from connectors.misp.target import MISPTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = MISPConnectorConfig(
        url=misp_url,
        api_key=misp_api_key
    )
    assert isinstance(config, ConnectorConfig), "MISPConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = MISPConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MISPConnector should be of type Connector"

    # get query target options
    misp_query_target_options = await connector.get_query_target_options()
    assert isinstance(misp_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select organizations to target
    org_selector = None
    for selector in misp_query_target_options.selectors:
        if selector.type == 'organization_ids':  
            org_selector = selector
            break

    assert org_selector, "failed to retrieve organization selector from query target options"

    assert isinstance(org_selector.values, list), "org_selector values must be a list"
    org_id = org_selector.values[0] if org_selector.values else None
    print(f"Selecting organization ID: {org_id}")

    assert org_id, f"failed to retrieve organization ID from organization selector"

    # set up the target with organization ID
    target = MISPTarget(organization_ids=[org_id])
    assert isinstance(target, ConnectorTargetInterface), "MISPTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_misp_iocs tool and execute it
    get_misp_iocs_tool = next(tool for tool in tools if tool.name == "get_misp_iocs")
    misp_iocs_result = await get_misp_iocs_tool.execute(organization_id=org_id)
    misp_iocs = misp_iocs_result.result

    print("Type of returned misp_iocs:", type(misp_iocs))
    print(f"len IOCs: {len(misp_iocs)} IOCs: {str(misp_iocs)[:200]}")

    # Verify that misp_iocs is a list
    assert isinstance(misp_iocs, list), "misp_iocs should be a list"
    assert len(misp_iocs) > 0, "misp_iocs should not be empty"
    
    # Limit the number of IOCs to check if there are many
    iocs_to_check = misp_iocs[:5] if len(misp_iocs) > 5 else misp_iocs
    
    # Verify structure of each IOC/attribute object
    for ioc in iocs_to_check:
        # Verify essential MISP attribute fields
        assert "id" in ioc, "Each IOC should have an 'id' field"
        assert "type" in ioc, "Each IOC should have a 'type' field"
        assert "value" in ioc, "Each IOC should have a 'value' field"
        assert "event_id" in ioc, "Each IOC should have an 'event_id' field"
        
        # Verify common MISP attribute fields
        assert "category" in ioc, "Each IOC should have a 'category' field"
        assert "to_ids" in ioc, "Each IOC should have a 'to_ids' field"
        assert "uuid" in ioc, "Each IOC should have a 'uuid' field"
        
        # Check for additional optional fields
        optional_fields = ["comment", "distribution", "sharing_group_id", "timestamp"]
        present_optional = [field for field in optional_fields if field in ioc]
        
        print(f"IOC {ioc['id']} (type: {ioc['type']}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first IOC for debugging
        if ioc == iocs_to_check[0]:
            print(f"Example IOC structure: {ioc}")

    print(f"Successfully retrieved and validated {len(misp_iocs)} MISP IOCs")

    return True