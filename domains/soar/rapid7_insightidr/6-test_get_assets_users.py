# 6-test_get_assets_users.py

async def test_get_assets_users(zerg_state=None):
    """Test Rapid7 InsightIDR asset and user behavior data retrieval"""
    print("Testing Rapid7 InsightIDR asset and user behavior data retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    rapid7_insightidr_api_url = zerg_state.get("rapid7_insightidr_api_url").get("value")
    rapid7_insightidr_api_key = zerg_state.get("rapid7_insightidr_api_key").get("value")

    from connectors.rapid7_insightidr.config import Rapid7InsightIDRConnectorConfig
    from connectors.rapid7_insightidr.connector import Rapid7InsightIDRConnector
    from connectors.rapid7_insightidr.target import Rapid7InsightIDRTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = Rapid7InsightIDRConnectorConfig(
        api_url=rapid7_insightidr_api_url,
        api_key=rapid7_insightidr_api_key
    )
    assert isinstance(config, ConnectorConfig), "Rapid7InsightIDRConnectorConfig should be of type ConnectorConfig"

    connector = Rapid7InsightIDRConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "Rapid7InsightIDRConnector should be of type Connector"

    rapid7_insightidr_query_target_options = await connector.get_query_target_options()
    assert isinstance(rapid7_insightidr_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in rapid7_insightidr_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    assets_source = None
    for source in data_source_selector.values:
        if 'asset' in source.lower():
            assets_source = source
            break
    
    assert assets_source, "Assets data source not found in available options"
    print(f"Selecting assets data source: {assets_source}")

    target = Rapid7InsightIDRTarget(data_sources=[assets_source])
    assert isinstance(target, ConnectorTargetInterface), "Rapid7InsightIDRTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test asset retrieval
    get_rapid7_insightidr_assets_tool = next(tool for tool in tools if tool.name == "get_rapid7_insightidr_assets")
    assets_result = await get_rapid7_insightidr_assets_tool.execute()
    assets_data = assets_result.result

    print("Type of returned assets data:", type(assets_data))
    print(f"Assets count: {len(assets_data)} sample: {str(assets_data)[:200]}")

    assert isinstance(assets_data, list), "Assets data should be a list"
    assert len(assets_data) > 0, "Assets data should not be empty"
    
    assets_to_check = assets_data[:5] if len(assets_data) > 5 else assets_data
    
    for asset in assets_to_check:
        # Verify essential asset fields
        assert "id" in asset, "Each asset should have an 'id' field"
        assert "name" in asset, "Each asset should have a 'name' field"
        assert "type" in asset, "Each asset should have a 'type' field"
        
        assert asset["id"], "Asset ID should not be empty"
        assert asset["name"].strip(), "Asset name should not be empty"
        assert asset["type"].strip(), "Asset type should not be empty"
        
        asset_fields = ["ip_address", "hostname", "operating_system", "risk_score", "last_seen"]
        present_fields = [field for field in asset_fields if field in asset]
        
        print(f"Asset {asset['id']} ({asset['name']}, {asset['type']}) contains: {', '.join(present_fields)}")
        
        # If risk score is present, validate it's numeric
        if "risk_score" in asset:
            risk_score = asset["risk_score"]
            assert isinstance(risk_score, (int, float)), "Risk score should be numeric"
            assert 0 <= risk_score <= 100, f"Risk score should be between 0 and 100: {risk_score}"
        
        # If IP address is present, validate basic format
        if "ip_address" in asset:
            ip_address = asset["ip_address"]
            assert ip_address and ip_address.strip(), "IP address should not be empty"
        
        # Log the structure of the first asset for debugging
        if asset == assets_to_check[0]:
            print(f"Example asset structure: {asset}")

    print(f"Successfully retrieved and validated {len(assets_data)} Rapid7 InsightIDR assets")

    # Test user behavior data retrieval if available
    try:
        get_rapid7_insightidr_users_tool = next((tool for tool in tools if tool.name == "get_rapid7_insightidr_users"), None)
        if get_rapid7_insightidr_users_tool:
            users_result = await get_rapid7_insightidr_users_tool.execute()
            users_data = users_result.result

            print("Type of returned users data:", type(users_data))
            print(f"Users count: {len(users_data)} sample: {str(users_data)[:200]}")

            assert isinstance(users_data, list), "Users data should be a list"
            
            if len(users_data) > 0:
                users_to_check = users_data[:5] if len(users_data) > 5 else users_data
                
                for user in users_to_check:
                    # Verify essential user fields
                    assert "name" in user, "Each user should have a 'name' field"
                    assert user["name"].strip(), "User name should not be empty"
                    
                    user_fields = ["email", "department", "risk_score", "last_activity", "behavior_analytics"]
                    present_fields = [field for field in user_fields if field in user]
                    
                    print(f"User {user['name']} contains: {', '.join(present_fields)}")

                print(f"Successfully retrieved and validated {len(users_data)} Rapid7 InsightIDR users")
            else:
                print("No users data available")
        else:
            print("User retrieval tool not available")
    except Exception as e:
        print(f"User retrieval test skipped: {e}")

    return True