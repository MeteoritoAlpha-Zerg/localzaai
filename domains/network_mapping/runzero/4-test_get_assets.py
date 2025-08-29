# 4-test_get_assets.py

async def test_get_assets(zerg_state=None):
    """Test RunZero asset inventory retrieval"""
    print("Testing RunZero asset inventory retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    runzero_api_url = zerg_state.get("runzero_api_url").get("value")
    runzero_api_token = zerg_state.get("runzero_api_token").get("value")
    runzero_organization_id = zerg_state.get("runzero_organization_id").get("value")

    from connectors.runzero.config import RunZeroConnectorConfig
    from connectors.runzero.connector import RunZeroConnector
    from connectors.runzero.target import RunZeroTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = RunZeroConnectorConfig(
        api_url=runzero_api_url,
        api_token=runzero_api_token,
        organization_id=runzero_organization_id
    )
    assert isinstance(config, ConnectorConfig), "RunZeroConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = RunZeroConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RunZeroConnector should be of type Connector"

    # get query target options
    runzero_query_target_options = await connector.get_query_target_options()
    assert isinstance(runzero_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select assets data source
    data_source_selector = None
    for selector in runzero_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find assets in available data sources
    assets_source = None
    for source in data_source_selector.values:
        if 'asset' in source.lower():
            assets_source = source
            break
    
    assert assets_source, "Assets data source not found in available options"
    print(f"Selecting assets data source: {assets_source}")

    # set up the target with assets data source
    target = RunZeroTarget(data_sources=[assets_source])
    assert isinstance(target, ConnectorTargetInterface), "RunZeroTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_runzero_assets tool
    runzero_get_assets_tool = next(tool for tool in tools if tool.name == "get_runzero_assets")
    assets_result = await runzero_get_assets_tool.execute()
    assets_data = assets_result.result

    print("Type of returned assets data:", type(assets_data))
    print(f"Assets count: {len(assets_data)} sample: {str(assets_data)[:200]}")

    # Verify that assets_data is a list
    assert isinstance(assets_data, list), "Assets data should be a list"
    assert len(assets_data) > 0, "Assets data should not be empty"
    
    # Limit the number of assets to check if there are many
    assets_to_check = assets_data[:5] if len(assets_data) > 5 else assets_data
    
    # Verify structure of each asset entry
    for asset in assets_to_check:
        # Verify essential asset fields per RunZero API specification
        assert "id" in asset, "Each asset should have an 'id' field"
        assert "addresses" in asset, "Each asset should have an 'addresses' field"
        
        # Verify addresses structure
        addresses = asset["addresses"]
        assert isinstance(addresses, list), "Addresses should be a list"
        assert len(addresses) > 0, "Asset should have at least one address"
        
        # Validate IP addresses
        for address in addresses:
            assert isinstance(address, str), "Each address should be a string"
            # Basic IP validation (IPv4 or IPv6)
            assert ('.' in address and len(address.split('.')) == 4) or ':' in address, f"Invalid IP address format: {address}"
        
        # Check for additional asset fields per RunZero specification
        asset_fields = ["names", "os", "hw", "type", "alive", "first_seen", "last_seen", "attributes"]
        present_fields = [field for field in asset_fields if field in asset]
        
        print(f"Asset {asset['id']} (IPs: {', '.join(addresses[:2])}) contains: {', '.join(present_fields)}")
        
        # If names are present, validate structure
        if "names" in asset:
            names = asset["names"]
            assert isinstance(names, list), "Names should be a list"
            for name in names:
                assert isinstance(name, str), "Each name should be a string"
                assert name.strip(), "Name should not be empty"
        
        # If OS is present, validate it's not empty
        if "os" in asset:
            os_info = asset["os"]
            assert os_info and os_info.strip(), "OS information should not be empty"
        
        # If type is present, validate it's a valid asset type
        if "type" in asset:
            asset_type = asset["type"]
            assert asset_type and asset_type.strip(), "Asset type should not be empty"
            # Common RunZero asset types
            valid_types = ["server", "desktop", "laptop", "mobile", "network", "printer", "iot", "unknown"]
            assert any(valid_type in asset_type.lower() for valid_type in valid_types), f"Unexpected asset type: {asset_type}"
        
        # If alive status is present, validate it's boolean
        if "alive" in asset:
            alive = asset["alive"]
            assert isinstance(alive, bool), "Alive status should be boolean"
        
        # If attributes are present, validate structure
        if "attributes" in asset:
            attributes = asset["attributes"]
            assert isinstance(attributes, dict), "Attributes should be a dictionary"
        
        # Log the structure of the first asset for debugging
        if asset == assets_to_check[0]:
            print(f"Example asset structure: {asset}")

    print(f"Successfully retrieved and validated {len(assets_data)} RunZero assets")

    return True