# 5-test_business_impact_retrieval.py

async def test_business_impact_retrieval(zerg_state=None):
    """Test Key Caliber business impact retrieval by way of connector tools"""
    print("Attempting to retrieve business impact assessments using Key Caliber connector")

    assert zerg_state, "this test requires valid zerg_state"

    keycaliber_host = zerg_state.get("keycaliber_host").get("value")
    keycaliber_api_key = zerg_state.get("keycaliber_api_key").get("value")

    from connectors.keycaliber.config import KeyCaliberConnectorConfig
    from connectors.keycaliber.connector import KeyCaliberConnector
    from connectors.keycaliber.tools import KeyCaliberConnectorTools, GetKeyCaliberBusinessImpactInput
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

    assert isinstance(asset_selector.values, list), "asset_selector values must be a list"
    asset_id = asset_selector.values[0] if asset_selector.values else None
    print(f"Selecting asset id: {asset_id}")

    assert asset_id, f"failed to retrieve asset id from asset selector"

    # set up the target with asset id
    target = KeyCaliberTarget(asset_ids=[asset_id])
    assert isinstance(target, ConnectorTargetInterface), "KeyCaliberTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_business_impact tool and execute it with asset id
    get_business_impact_tool = next(tool for tool in tools if tool.name == "get_business_impact")
    business_impact_result = await get_business_impact_tool.execute(asset_id=asset_id)
    business_impact = business_impact_result.result

    print("Type of returned business_impact:", type(business_impact))
    print(f"business impact: {str(business_impact)[:200]}")

    # Verify that business_impact is a dict/object
    assert isinstance(business_impact, dict), "business_impact should be a dict"
    assert business_impact, "business_impact should not be empty"
    
    # Verify structure of the business impact assessment object
    # Verify essential Key Caliber business impact assessment fields
    assert "asset_id" in business_impact, "Business impact assessment should have an 'asset_id' field"
    assert business_impact["asset_id"] == asset_id, f"Business impact asset_id {business_impact['asset_id']} does not match requested asset_id"
    
    # Verify common Key Caliber business impact assessment fields
    assert "criticality" in business_impact, "Business impact assessment should have a 'criticality' field"
    assert "financial_impact" in business_impact, "Business impact assessment should have a 'financial_impact' field"
    
    # Check for additional detailed fields that are typically available in business impact assessments
    detailed_fields = ["operational_impact", "reputational_impact", "regulatory_impact", "recovery_time_objective", "recovery_point_objective", "maximum_tolerable_downtime", "business_unit", "impact_category", "assessment_date", "assessor", "confidence_level", "scenario_type", "potential_loss_amount", "dependencies", "mitigation_strategies"]
    present_detailed = [field for field in detailed_fields if field in business_impact]
    
    print(f"Business impact assessment for asset {business_impact['asset_id']} contains these detailed fields: {', '.join(present_detailed)}")
    
    # Log the full structure for debugging
    print(f"Complete business impact assessment structure: {business_impact}")

    # Print some key information from the business impact assessment
    print(f"Retrieved business impact assessment for asset: {asset_id}")
    print(f"Criticality: {business_impact.get('criticality')}")
    print(f"Financial Impact: {business_impact.get('financial_impact')}")
    print(f"Operational Impact: {business_impact.get('operational_impact')}")

    print(f"Successfully retrieved and validated business impact assessment for Key Caliber asset {asset_id}")

    return True