# 4-test_asset_prioritization_retrieval.py

async def test_asset_prioritization_retrieval(zerg_state=None):
    """Test Key Caliber asset prioritization retrieval by way of connector tools"""
    print("Attempting to authenticate using Key Caliber connector")

    assert zerg_state, "this test requires valid zerg_state"

    keycaliber_host = zerg_state.get("keycaliber_host").get("value")
    keycaliber_api_key = zerg_state.get("keycaliber_api_key").get("value")

    from connectors.keycaliber.config import KeyCaliberConnectorConfig
    from connectors.keycaliber.connector import KeyCaliberConnector
    from connectors.keycaliber.tools import KeyCaliberConnectorTools
    from connectors.keycaliber.target import KeyCaliberTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = KeyCaliberConnectorConfig(
        host=keycaliber_host,
        api_key=keycaliber_api_key,
    )
    assert isinstance(config, ConnectorConfig), "KeyCaliberConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = KeyCaliberConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "KeyCaliberConnector should be of type Connector"

    # get query target options
    keycaliber_query_target_options = await connector.get_query_target_options()
    assert isinstance(keycaliber_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select assets to target
    asset_selector = None
    for selector in keycaliber_query_target_options.selectors:
        if selector.type == 'asset_ids':  
            asset_selector = selector
            break

    assert asset_selector, "failed to retrieve asset selector from query target options"

    # grab the first two assets 
    num_assets = 2
    assert isinstance(asset_selector.values, list), "asset_selector values must be a list"
    asset_ids = asset_selector.values[:num_assets] if asset_selector.values else None
    print(f"Selecting asset ids: {asset_ids}")

    assert asset_ids, f"failed to retrieve {num_assets} asset ids from asset selector"

    # set up the target with asset ids
    target = KeyCaliberTarget(asset_ids=asset_ids)
    assert isinstance(target, ConnectorTargetInterface), "KeyCaliberTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_asset_prioritization tool
    keycaliber_get_asset_prioritization_tool = next(tool for tool in tools if tool.name == "get_asset_prioritization")
    asset_prioritization_result = await keycaliber_get_asset_prioritization_tool.execute()
    asset_prioritization = asset_prioritization_result.result

    print("Type of returned asset_prioritization:", type(asset_prioritization))
    print(f"len assets: {len(asset_prioritization)} assets: {str(asset_prioritization)[:200]}")

    # ensure that asset_prioritization are a list of objects with the id being the asset id
    # and the object having the asset prioritization data and other relevant information from the keycaliber specification
    # as may be descriptive
    # Verify that asset_prioritization is a list
    assert isinstance(asset_prioritization, list), "asset_prioritization should be a list"
    assert len(asset_prioritization) > 0, "asset_prioritization should not be empty"
    assert len(asset_prioritization) == num_assets, f"asset_prioritization should have {num_assets} entries"
    
    # Verify structure of each asset prioritization object
    for asset in asset_prioritization:
        assert "asset_id" in asset, "Each asset should have an 'asset_id' field"
        assert asset["asset_id"] in asset_ids, f"Asset id {asset['asset_id']} is not in the requested asset_ids"
        
        # Verify essential Key Caliber asset prioritization fields
        # These are common fields in Key Caliber asset prioritization based on Key Caliber API specification
        assert "risk_score" in asset, "Each asset should have a 'risk_score' field"
        assert "criticality_level" in asset, "Each asset should have a 'criticality_level' field"
        
        # Check for additional descriptive fields (optional in some Key Caliber instances)
        descriptive_fields = ["asset_name", "asset_type", "business_unit", "location", "owner", "impact_score", "vulnerability_score", "threat_level", "priority_ranking", "last_assessed", "next_assessment_due"]
        present_fields = [field for field in descriptive_fields if field in asset]
        
        print(f"Asset {asset['asset_id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if asset == asset_prioritization[0]:
            print(f"Example asset prioritization structure: {asset}")

    print(f"Successfully retrieved and validated {len(asset_prioritization)} Key Caliber asset prioritization records")

    return True