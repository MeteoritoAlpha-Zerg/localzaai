async def test_security_cmdb_retrieval(zerg_state=None):
    """Test ServiceNow security-related CMDB item retrieval"""
    print("Retrieving security-related CMDB items using ServiceNow connector")

    assert zerg_state, "this test requires valid zerg_state"

    servicenow_instance_url = zerg_state.get("servicenow_instance_url").get("value")
    servicenow_client_id = zerg_state.get("servicenow_client_id").get("value")
    servicenow_client_secret = zerg_state.get("servicenow_client_secret").get("value")

    from connectors.servicenow.config import ServiceNowConnectorConfig
    from connectors.servicenow.connector import ServiceNowConnector
    from connectors.servicenow.tools import ServiceNowConnectorTools
    from connectors.servicenow.target import ServiceNowTarget

    config = ServiceNowConnectorConfig(
        instance_url=servicenow_instance_url,
        client_id=servicenow_client_id,
        client_secret=SecretStr(servicenow_client_secret)
    )
    connector = ServiceNowConnector(config)

    connector_target = ServiceNowTarget(config=config)
    
    # Get connector tools
    tools = ServiceNowConnectorTools(
        servicenow_config=config, 
        target=ServiceNowTarget, 
        connector_display_name="ServiceNow"
    )
    
    # Get security-relevant CMDB items
    security_asset_types = zerg_state.get("security_asset_types").get("value")
    
    all_security_assets = []
    
    # Iterate through different security asset types to find relevant CIs
    for asset_type in security_asset_types:
        try:
            # Query for specific security asset types
            query = f"sys_class_name={asset_type}"
            assets = await tools.query_servicenow_records(
                table_name="cmdb_ci",
                query=query
            )
            
            if assets:
                print(f"Found {len(assets)} {asset_type} assets")
                all_security_assets.extend(assets)
                
        except Exception as e:
            print(f"Error retrieving {asset_type} assets: {e}")
            continue
    
    # If no specific asset types found, try a generic security keyword search
    if not all_security_assets:
        try:
            security_query = "nameLIKEsecurity^ORshort_descriptionLIKEsecurity^ORasset_tagLIKEsecurity"
            security_items = await tools.query_servicenow_records(
                table_name="cmdb_ci",
                query=security_query
            )
            
            if security_items:
                print(f"Found {len(security_items)} security-related CMDB items using keyword search")
                all_security_assets.extend(security_items)
                
        except Exception as e:
            print(f"Error searching for security-related CMDB items: {e}")
    
    # Categorize the security assets by type
    asset_categories = {}
    for asset in all_security_assets:
        asset_class = asset.get('sys_class_name', 'Unknown')
        if asset_class not in asset_categories:
            asset_categories[asset_class] = 0
        asset_categories[asset_class] += 1
    
    print("Security asset categories found:")
    for category, count in asset_categories.items():
        print(f"  - {category}: {count} items")
    
    return True