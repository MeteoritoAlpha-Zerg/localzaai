# 4-test_get_scores.py

async def test_get_scores(zerg_state=None):
    """Test SecurityScorecard security scores retrieval"""
    print("Testing SecurityScorecard security scores retrieval")

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
    
    scores_source = None
    for source in data_source_selector.values:
        if 'score' in source.lower():
            scores_source = source
            break
    
    assert scores_source, "Scores data source not found in available options"
    print(f"Selecting scores data source: {scores_source}")

    target = SecurityScorecardTarget(data_sources=[scores_source])
    assert isinstance(target, ConnectorTargetInterface), "SecurityScorecardTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    securityscorecard_get_scores_tool = next(tool for tool in tools if tool.name == "get_securityscorecard_scores")
    scores_result = await securityscorecard_get_scores_tool.execute()
    scores_data = scores_result.result

    print("Type of returned scores data:", type(scores_data))
    print(f"Scores count: {len(scores_data)} sample: {str(scores_data)[:200]}")

    assert isinstance(scores_data, list), "Scores data should be a list"
    assert len(scores_data) > 0, "Scores data should not be empty"
    
    scores_to_check = scores_data[:5] if len(scores_data) > 5 else scores_data
    
    for score in scores_to_check:
        # Verify essential score fields per SecurityScorecard API specification
        assert "domain" in score, "Each score should have a 'domain' field"
        assert "score" in score, "Each score should have a 'score' field"
        assert "grade" in score, "Each score should have a 'grade' field"
        assert "date" in score, "Each score should have a 'date' field"
        
        assert score["domain"].strip(), "Domain should not be empty"
        assert score["date"], "Date should not be empty"
        
        # Verify score is within valid range (SecurityScorecard uses 0-100)
        score_value = score["score"]
        assert isinstance(score_value, (int, float)), "Score should be numeric"
        assert 0 <= score_value <= 100, f"Score should be between 0 and 100: {score_value}"
        
        # Verify grade is valid (SecurityScorecard uses A-F grading)
        valid_grades = ["A", "B", "C", "D", "F"]
        grade = score["grade"]
        assert grade in valid_grades, f"Invalid grade: {grade}"
        
        score_fields = ["industry", "size", "factors", "percentile", "last_seen"]
        present_fields = [field for field in score_fields if field in score]
        
        print(f"Score for {score['domain']} (score: {score['score']}, grade: {score['grade']}) contains: {', '.join(present_fields)}")
        
        # If factors are present, validate structure
        if "factors" in score:
            factors = score["factors"]
            assert isinstance(factors, dict), "Factors should be a dictionary"
            for factor_name, factor_data in factors.items():
                assert isinstance(factor_data, dict), f"Factor {factor_name} should be a dictionary"
                if "score" in factor_data:
                    factor_score = factor_data["score"]
                    assert isinstance(factor_score, (int, float)), f"Factor score should be numeric: {factor_score}"
                    assert 0 <= factor_score <= 100, f"Factor score should be between 0 and 100: {factor_score}"
        
        # If percentile is present, validate it's numeric
        if "percentile" in score:
            percentile = score["percentile"]
            assert isinstance(percentile, (int, float)), "Percentile should be numeric"
            assert 0 <= percentile <= 100, f"Percentile should be between 0 and 100: {percentile}"
        
        # Log the structure of the first score for debugging
        if score == scores_to_check[0]:
            print(f"Example score structure: {score}")

    print(f"Successfully retrieved and validated {len(scores_data)} SecurityScorecard scores")

    return True