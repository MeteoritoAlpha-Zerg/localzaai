# 7-test_deception_assets.py

async def test_deception_assets(zerg_state=None):
    """Test Acalvio deception assets and honeypots retrieval"""
    print("Attempting to authenticate using Acalvio connector")

    assert zerg_state, "this test requires valid zerg_state"

    acalvio_api_url = zerg_state.get("acalvio_api_url").get("value")
    acalvio_api_key = zerg_state.get("acalvio_api_key").get("value")
    acalvio_username = zerg_state.get("acalvio_username").get("value")
    acalvio_password = zerg_state.get("acalvio_password").get("value")
    acalvio_tenant_id = zerg_state.get("acalvio_tenant_id").get("value")

    from connectors.acalvio.config import AcalvioConnectorConfig
    from connectors.acalvio.connector import AcalvioConnector
    from connectors.acalvio.tools import AcalvioConnectorTools, GetDeceptionAssetsInput
    from connectors.acalvio.target import AcalvioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = AcalvioConnectorConfig(
        api_url=acalvio_api_url,
        api_key=acalvio_api_key,
        username=acalvio_username,
        password=acalvio_password,
        tenant_id=acalvio_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "AcalvioConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = AcalvioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "AcalvioConnectorConfig should be of type ConnectorConfig"

    # get query target options
    acalvio_query_target_options = await connector.get_query_target_options()
    assert isinstance(acalvio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select environment to target
    environment_selector = None
    for selector in acalvio_query_target_options.selectors:
        if selector.type == 'environment_ids':  
            environment_selector = selector
            break

    assert environment_selector, "failed to retrieve environment selector from query target options"

    assert isinstance(environment_selector.values, list), "environment_selector values must be a list"
    environment_id = environment_selector.values[0] if environment_selector.values else None
    print(f"Selecting environment id: {environment_id}")

    assert environment_id, f"failed to retrieve environment id from environment selector"

    # set up the target with environment id
    target = AcalvioTarget(environment_ids=[environment_id])
    assert isinstance(target, ConnectorTargetInterface), "AcalvioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_deception_assets tool and execute it with environment id
    get_deception_assets_tool = next(tool for tool in tools if tool.name == "get_deception_assets")
    deception_assets_result = await get_deception_assets_tool.execute(environment_id=environment_id)
    deception_assets = deception_assets_result.result

    print("Type of returned deception_assets:", type(deception_assets))
    print(f"len assets: {len(deception_assets)} assets: {str(deception_assets)[:200]}")

    # Verify that deception_assets is a list
    assert isinstance(deception_assets, list), "deception_assets should be a list"
    assert len(deception_assets) > 0, "deception_assets should not be empty"
    
    # Limit the number of assets to check if there are many
    assets_to_check = deception_assets[:5] if len(deception_assets) > 5 else deception_assets
    
    # Verify structure of each asset object
    for asset in assets_to_check:
        # Verify essential deception asset fields
        assert "id" in asset, "Each asset should have an 'id' field"
        assert "name" in asset, "Each asset should have a 'name' field"
        assert "type" in asset, "Each asset should have a 'type' field"
        assert "status" in asset, "Each asset should have a 'status' field"
        assert "environment_id" in asset, "Each asset should have an 'environment_id' field"
        
        # Check if asset belongs to the requested environment
        assert asset["environment_id"] == environment_id, f"Asset {asset['id']} does not belong to the requested environment_id"
        
        # Verify asset types
        valid_asset_types = ["honeypot", "decoy", "breadcrumb", "canary", "trap", "lure"]
        assert asset["type"].lower() in valid_asset_types, f"Asset type should be one of {valid_asset_types}"
        
        # Verify asset status
        valid_statuses = ["active", "inactive", "deployed", "pending", "error"]
        assert asset["status"].lower() in valid_statuses, f"Asset status should be one of {valid_statuses}"
        
        # Check for additional asset fields
        asset_fields = ["ip_address", "hostname", "os_type", "services", "deployment_date", "last_interaction", "interaction_count"]
        present_asset_fields = [field for field in asset_fields if field in asset]
        
        print(f"Asset {asset['id']} contains these fields: {', '.join(present_asset_fields)}")
        
        # Verify interaction data if present
        if "interaction_count" in asset:
            assert isinstance(asset["interaction_count"], int), "interaction_count should be an integer"
        
        # Verify services if present
        if "services" in asset:
            services = asset["services"]
            assert isinstance(services, list), "services should be a list"
            for service in services:
                if isinstance(service, dict):
                    assert "port" in service, "Each service should have a 'port' field"
                    assert "protocol" in service, "Each service should have a 'protocol' field"
        
        # Log the structure of the first asset for debugging
        if asset == assets_to_check[0]:
            print(f"Example asset structure: {asset}")

    print(f"Successfully retrieved and validated {len(deception_assets)} Acalvio deception assets")

    return True