# 7-test_risk_comparison_retrieval.py

async def test_risk_comparison_retrieval(zerg_state=None):
    """Test Key Caliber risk comparison retrieval by way of connector tools"""
    print("Retrieving risk comparison data using Key Caliber connector")

    assert zerg_state, "this test requires valid zerg_state"

    keycaliber_host = zerg_state.get("keycaliber_host").get("value")
    keycaliber_api_key = zerg_state.get("keycaliber_api_key").get("value")

    from connectors.keycaliber.config import KeyCaliberConnectorConfig
    from connectors.keycaliber.connector import KeyCaliberConnector
    from connectors.keycaliber.tools import KeyCaliberConnectorTools, GetKeyCaliberRiskComparisonInput
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

    # set up the target (risk comparison queries typically cover organizational scope)
    target = KeyCaliberTarget()
    assert isinstance(target, ConnectorTargetInterface), "KeyCaliberTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the compare_risk_scores tool and execute it with business unit groups
    compare_risk_scores_tool = next(tool for tool in tools if tool.name == "compare_risk_scores")
    business_units = ["IT", "Finance", "Operations", "HR", "Legal"]
    risk_comparison_result = await compare_risk_scores_tool.execute(groups=business_units)
    risk_comparison = risk_comparison_result.result

    print("Type of returned risk_comparison:", type(risk_comparison))
    print(f"risk comparison: {str(risk_comparison)[:200]}")

    # Verify that risk_comparison is a dict/object
    assert isinstance(risk_comparison, dict), "risk_comparison should be a dict"
    assert risk_comparison, "risk_comparison should not be empty"
    
    # Verify structure of the risk comparison object
    # Verify essential Key Caliber risk comparison fields
    assert "comparison_metadata" in risk_comparison, "Risk comparison should have a 'comparison_metadata' field"
    assert "group_comparisons" in risk_comparison, "Risk comparison should have a 'group_comparisons' field"
    
    # Verify group comparisons structure
    group_comparisons = risk_comparison["group_comparisons"]
    assert isinstance(group_comparisons, dict), "group_comparisons should be a dict"
    assert len(group_comparisons) > 0, "group_comparisons should not be empty"
    
    # Check for additional detailed fields that are typically available in risk comparisons
    detailed_fields = ["overall_risk_summary", "methodology", "assessment_date", "assessor", "confidence_level", "data_sources", "time_period", "risk_categories", "comparative_metrics", "trend_analysis", "recommendations", "outliers", "statistical_significance"]
    present_detailed = [field for field in detailed_fields if field in risk_comparison]
    
    print(f"Risk comparison contains these detailed fields: {', '.join(present_detailed)}")
    
    # Validate each group's risk data
    for group_name, group_data in group_comparisons.items():
        print(f"Analyzing risk data for group: {group_name}")
        
        # Verify essential group risk fields
        assert "average_risk_score" in group_data, f"Group {group_name} should have an 'average_risk_score' field"
        assert "asset_count" in group_data, f"Group {group_name} should have an 'asset_count' field"
        
        # Check for additional group-specific fields
        group_fields = ["risk_distribution", "critical_assets", "vulnerability_count", "compliance_score", "incident_history", "mitigation_effectiveness", "risk_trend", "peer_comparison"]
        present_group_fields = [field for field in group_fields if field in group_data]
        
        print(f"  Group {group_name} contains these fields: {', '.join(present_group_fields)}")
        print(f"  Average Risk Score: {group_data.get('average_risk_score')}")
        print(f"  Asset Count: {group_data.get('asset_count')}")

    # Perform risk comparison analysis
    risk_scores = {}
    asset_counts = {}
    
    for group_name, group_data in group_comparisons.items():
        if 'average_risk_score' in group_data:
            risk_scores[group_name] = group_data['average_risk_score']
        if 'asset_count' in group_data:
            asset_counts[group_name] = group_data['asset_count']

    # Find highest and lowest risk groups
    if risk_scores:
        highest_risk_group = max(risk_scores, key=risk_scores.get)
        lowest_risk_group = min(risk_scores, key=risk_scores.get)
        
        print(f"Highest risk group: {highest_risk_group} (Score: {risk_scores[highest_risk_group]})")
        print(f"Lowest risk group: {lowest_risk_group} (Score: {risk_scores[lowest_risk_group]})")
        
        # Calculate risk spread
        risk_spread = max(risk_scores.values()) - min(risk_scores.values())
        print(f"Risk score spread across groups: {risk_spread}")

    # Identify groups requiring immediate attention
    if risk_scores:
        high_risk_threshold = 70  # Configurable threshold
        high_risk_groups = [group for group, score in risk_scores.items() if score > high_risk_threshold]
        
        if high_risk_groups:
            print(f"Groups requiring immediate attention (score > {high_risk_threshold}): {', '.join(high_risk_groups)}")

    # Check for trend analysis if available
    if "trend_analysis" in risk_comparison:
        trend_data = risk_comparison["trend_analysis"]
        print(f"Trend analysis available covering: {trend_data.get('time_period', 'unspecified period')}")

    # Check for recommendations
    if "recommendations" in risk_comparison:
        recommendations = risk_comparison["recommendations"]
        if isinstance(recommendations, list) and recommendations:
            print("Top recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec}")

    # Log the full structure for debugging
    print(f"Complete risk comparison structure keys: {list(risk_comparison.keys())}")

    print(f"Successfully retrieved and validated Key Caliber risk comparison data across {len(group_comparisons)} business units")

    return True