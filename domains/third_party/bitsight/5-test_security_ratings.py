# 5-test_security_ratings.py

async def test_security_ratings(zerg_state=None):
    """Test BitSight security ratings and risk data retrieval"""
    print("Attempting to retrieve security ratings using BitSight connector")

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

    assert isinstance(company_selector.values, list), "company_selector values must be a list"
    company_guid = company_selector.values[0] if company_selector.values else None
    print(f"Selecting company GUID: {company_guid}")

    assert company_guid, f"failed to retrieve company GUID from company selector"

    target = BitSightTarget(company_guids=[company_guid])
    assert isinstance(target, ConnectorTargetInterface), "BitSightTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get security ratings
    get_bitsight_ratings_tool = next(tool for tool in tools if tool.name == "get_bitsight_ratings")
    bitsight_ratings_result = await get_bitsight_ratings_tool.execute(company_guid=company_guid)
    bitsight_ratings = bitsight_ratings_result.result

    print("Type of returned bitsight_ratings:", type(bitsight_ratings))
    print(f"Security ratings: {str(bitsight_ratings)[:200]}")

    assert isinstance(bitsight_ratings, dict), "bitsight_ratings should be a dictionary"
    assert "rating" in bitsight_ratings, "Ratings should contain rating field"
    assert "rating_date" in bitsight_ratings, "Ratings should contain rating_date field"
    
    # Verify rating is within valid range
    assert 250 <= bitsight_ratings["rating"] <= 900, f"Rating {bitsight_ratings['rating']} is not within valid range"
    
    rating_fields = ["risk_vectors", "rating_details", "industry_median", "percentile"]
    present_rating_fields = [field for field in rating_fields if field in bitsight_ratings]
    
    print(f"Security ratings contain these fields: {', '.join(present_rating_fields)}")

    # Test 2: Get risk vectors
    get_bitsight_risk_vectors_tool = next(tool for tool in tools if tool.name == "get_bitsight_risk_vectors")
    bitsight_risk_vectors_result = await get_bitsight_risk_vectors_tool.execute(company_guid=company_guid)
    bitsight_risk_vectors = bitsight_risk_vectors_result.result

    print("Type of returned bitsight_risk_vectors:", type(bitsight_risk_vectors))

    assert isinstance(bitsight_risk_vectors, list), "bitsight_risk_vectors should be a list"
    
    if len(bitsight_risk_vectors) > 0:
        vectors_to_check = bitsight_risk_vectors[:5] if len(bitsight_risk_vectors) > 5 else bitsight_risk_vectors
        
        for vector in vectors_to_check:
            assert "name" in vector, "Each risk vector should have a 'name' field"
            assert "grade" in vector, "Each risk vector should have a 'grade' field"
            assert "percentile" in vector, "Each risk vector should have a 'percentile' field"
            
            # Verify grade is valid (A, B, C, D, F)
            valid_grades = ["A", "B", "C", "D", "F"]
            assert vector["grade"] in valid_grades, f"Risk vector grade {vector['grade']} is not valid"
            
            vector_fields = ["rating", "rating_date", "display_url"]
            present_vector_fields = [field for field in vector_fields if field in vector]
            
            print(f"Risk vector {vector['name']} (grade: {vector['grade']}) contains these fields: {', '.join(present_vector_fields)}")

        print(f"Successfully retrieved and validated {len(bitsight_risk_vectors)} BitSight risk vectors")

    # Test 3: Get rating history
    get_bitsight_history_tool = next(tool for tool in tools if tool.name == "get_bitsight_rating_history")
    bitsight_history_result = await get_bitsight_history_tool.execute(
        company_guid=company_guid,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    bitsight_history = bitsight_history_result.result

    print("Type of returned bitsight_history:", type(bitsight_history))

    assert isinstance(bitsight_history, list), "bitsight_history should be a list"
    
    if len(bitsight_history) > 0:
        history_to_check = bitsight_history[:3] if len(bitsight_history) > 3 else bitsight_history
        
        for entry in history_to_check:
            assert "date" in entry, "Each history entry should have a 'date' field"
            assert "rating" in entry, "Each history entry should have a 'rating' field"
            
            # Verify rating is within valid range
            assert 250 <= entry["rating"] <= 900, f"Historical rating {entry['rating']} is not within valid range"
            
            print(f"Rating on {entry['date']}: {entry['rating']}")

        print(f"Successfully retrieved and validated {len(bitsight_history)} BitSight rating history entries")

    # Test 4: Get industry benchmarks
    get_bitsight_benchmarks_tool = next(tool for tool in tools if tool.name == "get_bitsight_benchmarks")
    bitsight_benchmarks_result = await get_bitsight_benchmarks_tool.execute(company_guid=company_guid)
    bitsight_benchmarks = bitsight_benchmarks_result.result

    print("Type of returned bitsight_benchmarks:", type(bitsight_benchmarks))

    assert isinstance(bitsight_benchmarks, dict), "bitsight_benchmarks should be a dictionary"
    
    if bitsight_benchmarks:
        benchmark_fields = ["industry_median", "percentile", "industry_size", "grade_distribution"]
        present_benchmark_fields = [field for field in benchmark_fields if field in bitsight_benchmarks]
        
        print(f"Industry benchmarks contain these fields: {', '.join(present_benchmark_fields)}")

    print("Successfully completed security ratings and risk data tests")

    return True