# 5-test_security_ratings.py

async def test_security_ratings(zerg_state=None):
    """Test UpGuard security ratings and risk data retrieval"""
    print("Attempting to retrieve security ratings using UpGuard connector")

    assert zerg_state, "this test requires valid zerg_state"

    upguard_url = zerg_state.get("upguard_url").get("value")
    upguard_api_key = zerg_state.get("upguard_api_key").get("value")

    from connectors.upguard.config import UpGuardConnectorConfig
    from connectors.upguard.connector import UpGuardConnector
    from connectors.upguard.tools import UpGuardConnectorTools
    from connectors.upguard.target import UpGuardTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = UpGuardConnectorConfig(
        url=upguard_url,
        api_key=upguard_api_key,
    )
    assert isinstance(config, ConnectorConfig), "UpGuardConnectorConfig should be of type ConnectorConfig"

    connector = UpGuardConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "UpGuardConnector should be of type Connector"

    upguard_query_target_options = await connector.get_query_target_options()
    assert isinstance(upguard_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    vendor_selector = None
    for selector in upguard_query_target_options.selectors:
        if selector.type == 'vendor_ids':  
            vendor_selector = selector
            break

    assert vendor_selector, "failed to retrieve vendor selector from query target options"

    assert isinstance(vendor_selector.values, list), "vendor_selector values must be a list"
    vendor_id = vendor_selector.values[0] if vendor_selector.values else None
    print(f"Selecting vendor ID: {vendor_id}")

    assert vendor_id, f"failed to retrieve vendor ID from vendor selector"

    target = UpGuardTarget(vendor_ids=[vendor_id])
    assert isinstance(target, ConnectorTargetInterface), "UpGuardTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get vendor risk scores
    get_upguard_risk_scores_tool = next(tool for tool in tools if tool.name == "get_upguard_risk_scores")
    upguard_risk_scores_result = await get_upguard_risk_scores_tool.execute(vendor_id=vendor_id)
    upguard_risk_scores = upguard_risk_scores_result.result

    print("Type of returned upguard_risk_scores:", type(upguard_risk_scores))
    print(f"Risk scores: {str(upguard_risk_scores)[:200]}")

    assert isinstance(upguard_risk_scores, dict), "upguard_risk_scores should be a dictionary"
    assert "score" in upguard_risk_scores, "Risk scores should contain score field"
    assert "grade" in upguard_risk_scores, "Risk scores should contain grade field"
    
    # Verify score is within valid range
    assert 0 <= upguard_risk_scores["score"] <= 950, f"Score {upguard_risk_scores['score']} is not within valid range"
    
    # Verify grade is valid (A, B, C, D, F)
    valid_grades = ["A", "B", "C", "D", "F"]
    assert upguard_risk_scores["grade"] in valid_grades, f"Grade {upguard_risk_scores['grade']} is not valid"
    
    score_fields = ["percentile", "industry_percentile", "last_scanned", "score_date"]
    present_score_fields = [field for field in score_fields if field in upguard_risk_scores]
    
    print(f"Risk scores contain these fields: {', '.join(present_score_fields)}")

    # Test 2: Get risk factors
    get_upguard_risk_factors_tool = next(tool for tool in tools if tool.name == "get_upguard_risk_factors")
    upguard_risk_factors_result = await get_upguard_risk_factors_tool.execute(vendor_id=vendor_id)
    upguard_risk_factors = upguard_risk_factors_result.result

    print("Type of returned upguard_risk_factors:", type(upguard_risk_factors))

    assert isinstance(upguard_risk_factors, list), "upguard_risk_factors should be a list"
    
    if len(upguard_risk_factors) > 0:
        factors_to_check = upguard_risk_factors[:5] if len(upguard_risk_factors) > 5 else upguard_risk_factors
        
        for factor in factors_to_check:
            assert "name" in factor, "Each risk factor should have a 'name' field"
            assert "category" in factor, "Each risk factor should have a 'category' field"
            assert "severity" in factor, "Each risk factor should have a 'severity' field"
            
            valid_severities = ["high", "medium", "low", "info"]
            assert factor["severity"] in valid_severities, f"Risk factor severity {factor['severity']} is not valid"
            
            factor_fields = ["description", "evidence", "remediation", "first_seen", "last_seen"]
            present_factor_fields = [field for field in factor_fields if field in factor]
            
            print(f"Risk factor {factor['name']} ({factor['severity']}) contains these fields: {', '.join(present_factor_fields)}")

        print(f"Successfully retrieved and validated {len(upguard_risk_factors)} UpGuard risk factors")

    # Test 3: Get score trends
    get_upguard_trends_tool = next(tool for tool in tools if tool.name == "get_upguard_score_trends")
    upguard_trends_result = await get_upguard_trends_tool.execute(
        vendor_id=vendor_id,
        days=90
    )
    upguard_trends = upguard_trends_result.result

    print("Type of returned upguard_trends:", type(upguard_trends))

    assert isinstance(upguard_trends, list), "upguard_trends should be a list"
    
    if len(upguard_trends) > 0:
        trends_to_check = upguard_trends[:5] if len(upguard_trends) > 5 else upguard_trends
        
        for trend in trends_to_check:
            assert "date" in trend, "Each trend entry should have a 'date' field"
            assert "score" in trend, "Each trend entry should have a 'score' field"
            
            # Verify score is within valid range
            assert 0 <= trend["score"] <= 950, f"Trend score {trend['score']} is not within valid range"
            
            print(f"Score on {trend['date']}: {trend['score']}")

        print(f"Successfully retrieved and validated {len(upguard_trends)} UpGuard score trend entries")

    # Test 4: Get industry benchmarks
    get_upguard_benchmarks_tool = next(tool for tool in tools if tool.name == "get_upguard_benchmarks")
    upguard_benchmarks_result = await get_upguard_benchmarks_tool.execute(vendor_id=vendor_id)
    upguard_benchmarks = upguard_benchmarks_result.result

    print("Type of returned upguard_benchmarks:", type(upguard_benchmarks))

    assert isinstance(upguard_benchmarks, dict), "upguard_benchmarks should be a dictionary"
    
    if upguard_benchmarks:
        benchmark_fields = ["industry_average", "industry_median", "percentile", "peer_comparison"]
        present_benchmark_fields = [field for field in benchmark_fields if field in upguard_benchmarks]
        
        print(f"Industry benchmarks contain these fields: {', '.join(present_benchmark_fields)}")

    print("Successfully completed security ratings and risk data tests")

    return True