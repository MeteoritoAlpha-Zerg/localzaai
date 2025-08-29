# 4-test_list_companies.py

async def test_list_companies(zerg_state=None):
    """Test BitSight company and portfolio enumeration by way of connector tools"""
    print("Attempting to authenticate using BitSight connector")

    assert zerg_state, "this test requires valid zerg_state"

    bitsight_url = zerg_state.get("bitsight_url").get("value")
    bitsight_api_token = zerg_state.get("bitsight_api_token").get("value")

    from connectors.bitsight.config import BitSightConnectorConfig
    from connectors.bitsight.connector import BitSightConnector
    from connectors.bitsight.tools import BitSightConnectorTools
    from connectors.bitsight.target import BitSightTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = BitSightConnectorConfig(
        url=bitsight_url,
        api_token=bitsight_api_token,
    )
    assert isinstance(config, ConnectorConfig), "BitSightConnectorConfig should be of type ConnectorConfig"

    connector = BitSightConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "BitSightConnector should be of type Connector"

    bitsight_query_target_options = await connector.get_query_target_options()
    assert isinstance(bitsight_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    company_selector = None
    for selector in bitsight_query_target_options.selectors:
        if selector.type == 'company_guids':  
            company_selector = selector
            break

    assert company_selector, "failed to retrieve company selector from query target options"

    num_companies = 2
    assert isinstance(company_selector.values, list), "company_selector values must be a list"
    company_guids = company_selector.values[:num_companies] if company_selector.values else None
    print(f"Selecting company GUIDs: {company_guids}")

    assert company_guids, f"failed to retrieve {num_companies} company GUIDs from company selector"

    target = BitSightTarget(company_guids=company_guids)
    assert isinstance(target, ConnectorTargetInterface), "BitSightTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    bitsight_get_companies_tool = next(tool for tool in tools if tool.name == "get_bitsight_companies")
    bitsight_companies_result = await bitsight_get_companies_tool.execute()
    bitsight_companies = bitsight_companies_result.result

    print("Type of returned bitsight_companies:", type(bitsight_companies))
    print(f"len companies: {len(bitsight_companies)} companies: {str(bitsight_companies)[:200]}")

    assert isinstance(bitsight_companies, list), "bitsight_companies should be a list"
    assert len(bitsight_companies) > 0, "bitsight_companies should not be empty"
    assert len(bitsight_companies) == num_companies, f"bitsight_companies should have {num_companies} entries"
    
    for company in bitsight_companies:
        assert "guid" in company, "Each company should have a 'guid' field"
        assert company["guid"] in company_guids, f"Company GUID {company['guid']} is not in the requested company_guids"
        assert "name" in company, "Each company should have a 'name' field"
        assert "rating" in company, "Each company should have a 'rating' field"
        
        # Verify rating is within valid range (250-900)
        assert 250 <= company["rating"] <= 900, f"Company rating {company['rating']} is not within valid range 250-900"
        
        descriptive_fields = ["industry", "size", "country", "shortname", "permalink", "subscription_type"]
        present_fields = [field for field in descriptive_fields if field in company]
        
        print(f"Company {company['name']} (rating: {company['rating']}) contains these descriptive fields: {', '.join(present_fields)}")
        
        if company == bitsight_companies[0]:
            print(f"Example company structure: {company}")

    print(f"Successfully retrieved and validated {len(bitsight_companies)} BitSight companies")

    # Test portfolios as well
    get_bitsight_portfolios_tool = next(tool for tool in tools if tool.name == "get_bitsight_portfolios")
    bitsight_portfolios_result = await get_bitsight_portfolios_tool.execute()
    bitsight_portfolios = bitsight_portfolios_result.result

    print("Type of returned bitsight_portfolios:", type(bitsight_portfolios))

    assert isinstance(bitsight_portfolios, list), "bitsight_portfolios should be a list"
    
    if len(bitsight_portfolios) > 0:
        portfolios_to_check = bitsight_portfolios[:3] if len(bitsight_portfolios) > 3 else bitsight_portfolios
        
        for portfolio in portfolios_to_check:
            assert "guid" in portfolio, "Each portfolio should have a 'guid' field"
            assert "name" in portfolio, "Each portfolio should have a 'name' field"
            
            portfolio_fields = ["description", "company_count", "folder_guid", "is_bundle"]
            present_portfolio_fields = [field for field in portfolio_fields if field in portfolio]
            
            print(f"Portfolio {portfolio['name']} contains these fields: {', '.join(present_portfolio_fields)}")
        
        print(f"Successfully retrieved and validated {len(bitsight_portfolios)} BitSight portfolios")

    return True