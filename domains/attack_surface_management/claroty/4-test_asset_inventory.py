# 4-test_asset_inventory.py

async def test_asset_inventory(zerg_state=None):
    """Test Claroty OT/ICS asset inventory retrieval by way of connector tools"""
    print("Attempting to authenticate using Claroty connector")

    assert zerg_state, "this test requires valid zerg_state"

    claroty_server_url = zerg_state.get("claroty_server_url").get("value")
    claroty_api_token = zerg_state.get("claroty_api_token").get("value")
    claroty_username = zerg_state.get("claroty_username").get("value")
    claroty_password = zerg_state.get("claroty_password").get("value")
    claroty_api_version = zerg_state.get("claroty_api_version").get("value")

    from connectors.claroty.config import ClarotyConnectorConfig
    from connectors.claroty.connector import ClarotyConnector
    from connectors.claroty.tools import ClarotyConnectorTools
    from connectors.claroty.target import ClarotyTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = ClarotyConnectorConfig(
        server_url=claroty_server_url,
        api_token=claroty_api_token,
        username=claroty_username,
        password=claroty_password,
        api_version=claroty_api_version
    )
    assert isinstance(config, ConnectorConfig), "ClarotyConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ClarotyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ClarotyConnector should be of type Connector"

    # get query target options
    claroty_query_target_options = await connector.get_query_target_options()
    assert isinstance(claroty_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select asset types to target
    asset_type_selector = None
    for selector in claroty_query_target_options.selectors:
        if selector.type == 'asset_types':  
            asset_type_selector = selector
            break

    assert asset_type_selector, "failed to retrieve asset type selector from query target options"

    # grab the first two asset types 
    num_asset_types = 2
    assert isinstance(asset_type_selector.values, list), "asset_type_selector values must be a list"
    asset_types = asset_type_selector.values[:num_asset_types] if asset_type_selector.values else None
    print(f"Selecting asset types: {asset_types}")

    assert asset_types, f"failed to retrieve {num_asset_types} asset types from asset type selector"

    # select security zones to target
    zone_selector = None
    for selector in claroty_query_target_options.selectors:
        if selector.type == 'security_zones':  
            zone_selector = selector
            break

    # Security zones might be optional in some Claroty deployments
    security_zones = None
    if zone_selector and isinstance(zone_selector.values, list) and zone_selector.values:
        security_zones = zone_selector.values[:1]  # Select first zone
        print(f"Selecting security zones: {security_zones}")

    # set up the target with asset types and security zones
    target = ClarotyTarget(asset_types=asset_types, security_zones=security_zones)
    assert isinstance(target, ConnectorTargetInterface), "ClarotyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_claroty_assets tool
    claroty_get_assets_tool = next(tool for tool in tools if tool.name == "get_claroty_assets")
    claroty_assets_result = await claroty_get_assets_tool.execute()
    claroty_assets = claroty_assets_result.result

    print("Type of returned claroty_assets:", type(claroty_assets))
    print(f"len assets: {len(claroty_assets)} assets: {str(claroty_assets)[:200]}")

    # ensure that claroty_assets are a list of objects with OT/ICS asset information
    # and the object having the asset details and operational information from the claroty specification
    # as may be descriptive
    # Verify that claroty_assets is a list
    assert isinstance(claroty_assets, list), "claroty_assets should be a list"
    assert len(claroty_assets) > 0, "claroty_assets should not be empty"
    
    # Limit the number of assets to check if there are many
    assets_to_check = claroty_assets[:5] if len(claroty_assets) > 5 else claroty_assets
    
    # Verify structure of each asset object
    for asset in assets_to_check:
        assert "id" in asset, "Each asset should have an 'id' field"
        assert "name" in asset, "Each asset should have a 'name' field"
        
        # Verify essential OT/ICS asset fields
        # These are common fields in Claroty assets based on OT/ICS specifications
        assert "ip_address" in asset, "Each asset should have an 'ip_address' field"
        assert "asset_type" in asset, "Each asset should have an 'asset_type' field"
        
        # Check that asset type is one of the requested types
        assert asset["asset_type"] in asset_types, f"Asset type {asset['asset_type']} is not in the requested asset_types"
        
        # Check for additional essential OT/ICS fields
        essential_fields = ["mac_address", "vendor", "model", "firmware_version"]
        present_essential = [field for field in essential_fields if field in asset]
        print(f"Asset {asset['name']} contains these essential fields: {', '.join(present_essential)}")
        
        # Check for network and protocol information
        network_fields = ["subnet", "vlan", "protocols", "services"]
        present_network = [field for field in network_fields if field in asset]
        print(f"Asset {asset['name']} contains these network fields: {', '.join(present_network)}")
        
        # Check for security zone if zones were selected
        if security_zones:
            zone_fields = ["security_zone", "zone_id", "network_segment"]
            present_zone = [field for field in zone_fields if field in asset]
            print(f"Asset {asset['name']} contains these zone fields: {', '.join(present_zone)}")
        
        # Check for operational and status information
        operational_fields = ["status", "last_seen", "operational_state", "criticality"]
        present_operational = [field for field in operational_fields if field in asset]
        print(f"Asset {asset['name']} contains these operational fields: {', '.join(present_operational)}")
        
        # Check for vulnerability and risk information
        risk_fields = ["risk_score", "vulnerabilities", "patch_level", "security_status"]
        present_risk = [field for field in risk_fields if field in asset]
        print(f"Asset {asset['name']} contains these risk fields: {', '.join(present_risk)}")
        
        # Log the full structure of the first asset
        if asset == assets_to_check[0]:
            print(f"Example asset structure: {asset}")

    print(f"Successfully retrieved and validated {len(claroty_assets)} Claroty OT/ICS assets")

    return True