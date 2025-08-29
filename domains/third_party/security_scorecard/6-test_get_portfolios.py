# 6-test_get_portfolios.py

async def test_get_portfolios(zerg_state=None):
    """Test SecurityScorecard vendor risk intelligence and portfolio data retrieval"""
    print("Testing SecurityScorecard vendor risk intelligence and portfolio data retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    securityscorecard_api_url = zerg_state.get("securityscorecard_api_url").get("value")
    securityscorecard_api_token = zerg_state.get("securityscorecard_api_token").get("value")

    from connectors.securityscorecard.config import SecurityScorecardConnectorConfig
    from connectors.securityscorecard.connector import SecurityScorecardConnector
    from connectors.securityscorecard.target import SecurityScorecardTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = SecurityScorecardConnectorConfig(
        api_url=securityscorecard_api_url,
        api_token=securityscorecard_api_token
    )
    assert isinstance(config, ConnectorConfig), "SecurityScorecardConnectorConfig should be of type ConnectorConfig"

    connector = SecurityScorecardConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SecurityScorecardConnector should be of type Connector"

    securityscorecard_query_target_options = await connector.get_query_target_options()
    assert isinstance(securityscorecard_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in securityscorecard_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    portfolios_source = None
    for source in data_source_selector.values:
        if 'portfolio' in source.lower():
            portfolios_source = source
            break
    
    assert portfolios_source, "Portfolios data source not found in available options"
    print(f"Selecting portfolios data source: {portfolios_source}")

    target = SecurityScorecardTarget(data_sources=[portfolios_source])
    assert isinstance(target, ConnectorTargetInterface), "SecurityScorecardTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test portfolio retrieval
    get_securityscorecard_portfolios_tool = next(tool for tool in tools if tool.name == "get_securityscorecard_portfolios")
    portfolios_result = await get_securityscorecard_portfolios_tool.execute()
    portfolios_data = portfolios_result.result

    print("Type of returned portfolios data:", type(portfolios_data))
    print(f"Portfolios count: {len(portfolios_data)} sample: {str(portfolios_data)[:200]}")

    assert isinstance(portfolios_data, list), "Portfolios data should be a list"
    assert len(portfolios_data) > 0, "Portfolios data should not be empty"
    
    portfolios_to_check = portfolios_data[:5] if len(portfolios_data) > 5 else portfolios_data
    
    for portfolio in portfolios_to_check:
        # Verify essential portfolio fields per SecurityScorecard API specification
        assert "id" in portfolio, "Each portfolio should have an 'id' field"
        assert "name" in portfolio, "Each portfolio should have a 'name' field"
        assert "created" in portfolio, "Each portfolio should have a 'created' field"
        
        assert portfolio["id"], "Portfolio ID should not be empty"
        assert portfolio["name"].strip(), "Portfolio name should not be empty"
        assert portfolio["created"], "Created date should not be empty"
        
        portfolio_fields = ["description", "company_count", "average_score", "vendors", "tags"]
        present_fields = [field for field in portfolio_fields if field in portfolio]
        
        print(f"Portfolio {portfolio['id']} ({portfolio['name']}) contains: {', '.join(present_fields)}")
        
        # If company count is present, verify it's numeric
        if "company_count" in portfolio:
            company_count = portfolio["company_count"]
            assert isinstance(company_count, int), "Company count should be an integer"
            assert company_count >= 0, "Company count should be non-negative"
        
        # If average score is present, validate it's within valid range
        if "average_score" in portfolio:
            avg_score = portfolio["average_score"]
            assert isinstance(avg_score, (int, float)), "Average score should be numeric"
            assert 0 <= avg_score <= 100, f"Average score should be between 0 and 100: {avg_score}"
        
        # If vendors are present, validate structure
        if "vendors" in portfolio:
            vendors = portfolio["vendors"]
            assert isinstance(vendors, list), "Vendors should be a list"
            for vendor in vendors:
                assert isinstance(vendor, dict), "Each vendor should be a dictionary"
                assert "domain" in vendor, "Each vendor should have a domain"
                assert vendor["domain"].strip(), "Vendor domain should not be empty"
        
        # If tags are present, validate structure
        if "tags" in portfolio:
            tags = portfolio["tags"]
            assert isinstance(tags, list), "Tags should be a list"
            for tag in tags:
                assert isinstance(tag, str), "Each tag should be a string"
                assert tag.strip(), "Tag should not be empty"
        
        # Log the structure of the first portfolio for debugging
        if portfolio == portfolios_to_check[0]:
            print(f"Example portfolio structure: {portfolio}")

    print(f"Successfully retrieved and validated {len(portfolios_data)} SecurityScorecard portfolios")

    # Test vendor risk data retrieval if available
    try:
        get_securityscorecard_vendors_tool = next((tool for tool in tools if tool.name == "get_securityscorecard_vendors"), None)
        if get_securityscorecard_vendors_tool:
            vendors_result = await get_securityscorecard_vendors_tool.execute()
            vendors_data = vendors_result.result

            print("Type of returned vendors data:", type(vendors_data))
            print(f"Vendors count: {len(vendors_data)} sample: {str(vendors_data)[:200]}")

            assert isinstance(vendors_data, list), "Vendors data should be a list"
            
            if len(vendors_data) > 0:
                vendors_to_check = vendors_data[:5] if len(vendors_data) > 5 else vendors_data
                
                for vendor in vendors_to_check:
                    # Verify essential vendor fields
                    assert "domain" in vendor, "Each vendor should have a 'domain' field"
                    assert vendor["domain"].strip(), "Vendor domain should not be empty"
                    
                    vendor_fields = ["name", "score", "grade", "risk_factors", "industry"]
                    present_fields = [field for field in vendor_fields if field in vendor]
                    
                    print(f"Vendor {vendor['domain']} contains: {', '.join(present_fields)}")

                print(f"Successfully retrieved and validated {len(vendors_data)} SecurityScorecard vendors")
            else:
                print("No vendors data available")
        else:
            print("Vendor retrieval tool not available")
    except Exception as e:
        print(f"Vendor retrieval test skipped: {e}")

    return True