# 4-test_list_organizations.py

async def test_list_organizations(zerg_state=None):
    """Test Hubble organization and asset group enumeration by way of connector tools"""
    print("Attempting to authenticate using Hubble connector")

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

    # grab the first two organizations 
    num_organizations = 2
    assert isinstance(organization_selector.values, list), "organization_selector values must be a list"
    organization_ids = organization_selector.values[:num_organizations] if organization_selector.values else None
    print(f"Selecting organization IDs: {organization_ids}")

    assert organization_ids, f"failed to retrieve {num_organizations} organization IDs from organization selector"

    # set up the target with organization IDs
    target = HubbleTarget(organization_ids=organization_ids)
    assert isinstance(target, ConnectorTargetInterface), "HubbleTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_hubble_organizations tool
    hubble_get_organizations_tool = next(tool for tool in tools if tool.name == "get_hubble_organizations")
    hubble_organizations_result = await hubble_get_organizations_tool.execute()
    hubble_organizations = hubble_organizations_result.result

    print("Type of returned hubble_organizations:", type(hubble_organizations))
    print(f"len organizations: {len(hubble_organizations)} organizations: {str(hubble_organizations)[:200]}")

    # Verify that hubble_organizations is a list
    assert isinstance(hubble_organizations, list), "hubble_organizations should be a list"
    assert len(hubble_organizations) > 0, "hubble_organizations should not be empty"
    assert len(hubble_organizations) == num_organizations, f"hubble_organizations should have {num_organizations} entries"
    
    # Verify structure of each organization object
    for organization in hubble_organizations:
        assert "id" in organization, "Each organization should have an 'id' field"
        assert organization["id"] in organization_ids, f"Organization ID {organization['id']} is not in the requested organization_ids"
        
        # Verify essential Hubble organization fields
        assert "name" in organization, "Each organization should have a 'name' field"
        assert "risk_score" in organization, "Each organization should have a 'risk_score' field"
        assert "industry" in organization, "Each organization should have an 'industry' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["description", "size", "country", "created_at", "updated_at", "compliance_status", "security_posture"]
        present_fields = [field for field in descriptive_fields if field in organization]
        
        print(f"Organization {organization['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first organization
        if organization == hubble_organizations[0]:
            print(f"Example organization structure: {organization}")

    print(f"Successfully retrieved and validated {len(hubble_organizations)} Hubble organizations")

    # Test asset groups as well
    get_hubble_asset_groups_tool = next(tool for tool in tools if tool.name == "get_hubble_asset_groups")
    hubble_asset_groups_result = await get_hubble_asset_groups_tool.execute()
    hubble_asset_groups = hubble_asset_groups_result.result

    print("Type of returned hubble_asset_groups:", type(hubble_asset_groups))
    
    # Verify asset groups structure
    assert isinstance(hubble_asset_groups, list), "hubble_asset_groups should be a list"
    
    if len(hubble_asset_groups) > 0:
        # Check first few asset groups
        groups_to_check = hubble_asset_groups[:3] if len(hubble_asset_groups) > 3 else hubble_asset_groups
        
        for group in groups_to_check:
            assert "id" in group, "Each asset group should have an 'id' field"
            assert "name" in group, "Each asset group should have a 'name' field"
            assert "organization_id" in group, "Each asset group should have an 'organization_id' field"
            
            # Check for additional asset group fields
            group_fields = ["asset_count", "risk_level", "category", "tags", "created_at"]
            present_group_fields = [field for field in group_fields if field in group]
            
            print(f"Asset group {group['name']} contains these fields: {', '.join(present_group_fields)}")
        
        print(f"Successfully retrieved and validated {len(hubble_asset_groups)} Hubble asset groups")

    return True