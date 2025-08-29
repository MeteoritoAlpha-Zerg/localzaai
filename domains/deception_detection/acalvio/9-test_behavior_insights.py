# 9-test_behavior_insights.py

async def test_behavior_insights(zerg_state=None):
    """Test Acalvio attacker behavior insights processing and analysis"""
    print("Attempting to authenticate using Acalvio connector")

    assert zerg_state, "this test requires valid zerg_state"

    acalvio_api_url = zerg_state.get("acalvio_api_url").get("value")
    acalvio_api_key = zerg_state.get("acalvio_api_key").get("value")
    acalvio_username = zerg_state.get("acalvio_username").get("value")
    acalvio_password = zerg_state.get("acalvio_password").get("value")
    acalvio_tenant_id = zerg_state.get("acalvio_tenant_id").get("value")

    from connectors.acalvio.config import AcalvioConnectorConfig
    from connectors.acalvio.connector import AcalvioConnector
    from connectors.acalvio.tools import AcalvioConnectorTools, GetBehaviorInsightsInput
    from connectors.acalvio.target import AcalvioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

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

    # set up the target (behavior insights can be global or environment-specific)
    target = AcalvioTarget()
    assert isinstance(target, ConnectorTargetInterface), "AcalvioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_behavior_insights tool
    get_behavior_insights_tool = next(tool for tool in tools if tool.name == "get_behavior_insights")
    behavior_insights_result = await get_behavior_insights_tool.execute()
    behavior_insights = behavior_insights_result.result

    print("Type of returned behavior_insights:", type(behavior_insights))
    print(f"Behavior insights keys: {list(behavior_insights.keys()) if isinstance(behavior_insights, dict) else 'Not a dict'}")

    # Verify that behavior_insights is a dictionary
    assert isinstance(behavior_insights, dict), "behavior_insights should be a dict"
    
    # Verify essential behavior insights fields
    assert "attacker_profiles" in behavior_insights, "Behavior insights should have 'attacker_profiles'"
    assert "behavioral_patterns" in behavior_insights, "Behavior insights should have 'behavioral_patterns'"
    assert "attack_methodologies" in behavior_insights, "Behavior insights should have 'attack_methodologies'"
    
    # Verify attacker profiles structure
    attacker_profiles = behavior_insights["attacker_profiles"]
    assert isinstance(attacker_profiles, list), "attacker_profiles should be a list"
    
    if len(attacker_profiles) > 0:
        # Check structure of attacker profiles
        for profile in attacker_profiles[:3]:  # Check first 3 profiles
            assert "profile_id" in profile, "Each profile should have a 'profile_id'"
            assert "skill_level" in profile, "Each profile should have a 'skill_level'"
            assert "primary_tactics" in profile, "Each profile should have 'primary_tactics'"
            
            # Verify skill levels
            valid_skill_levels = ["novice", "intermediate", "advanced", "expert"]
            assert profile["skill_level"].lower() in valid_skill_levels, f"Skill level should be one of {valid_skill_levels}"
            
            # Check for additional profile fields
            profile_fields = ["geographic_origin", "target_preferences", "tools_used", "dwell_time", "attack_frequency"]
            present_profile_fields = [field for field in profile_fields if field in profile]
            print(f"Attacker profile {profile['profile_id']} contains: {', '.join(present_profile_fields)}")
    
    # Verify behavioral patterns structure
    behavioral_patterns = behavior_insights["behavioral_patterns"]
    assert isinstance(behavioral_patterns, list), "behavioral_patterns should be a list"
    
    if len(behavioral_patterns) > 0:
        # Check structure of behavioral patterns
        for pattern in behavioral_patterns[:3]:  # Check first 3 patterns
            assert "pattern_id" in pattern, "Each pattern should have a 'pattern_id'"
            assert "pattern_name" in pattern, "Each pattern should have a 'pattern_name'"
            assert "frequency" in pattern, "Each pattern should have a 'frequency'"
            assert "confidence_score" in pattern, "Each pattern should have a 'confidence_score'"
            
            # Verify confidence score is within valid range
            confidence = pattern["confidence_score"]
            assert 0 <= confidence <= 1, f"Confidence score should be between 0 and 1, got {confidence}"
    
    # Verify attack methodologies structure
    attack_methodologies = behavior_insights["attack_methodologies"]
    assert isinstance(attack_methodologies, dict), "attack_methodologies should be a dict"
    
    # Check for common attack methodology categories
    methodology_categories = ["reconnaissance", "initial_access", "persistence", "lateral_movement", "exfiltration"]
    present_methodologies = [cat for cat in methodology_categories if cat in attack_methodologies]
    print(f"Attack methodologies contains these categories: {', '.join(present_methodologies)}")
    
    # Verify methodology details
    for category in present_methodologies[:3]:  # Check first 3 categories
        methods = attack_methodologies[category]
        assert isinstance(methods, list), f"{category} methods should be a list"
        
        for method in methods[:2]:  # Check first 2 methods in each category
            if isinstance(method, dict):
                assert "technique" in method, f"Each {category} method should have a 'technique'"
                assert "prevalence" in method, f"Each {category} method should have a 'prevalence'"
    
    # Check for advanced analytics fields
    analytics_fields = ["trend_analysis", "anomaly_detection", "predictive_indicators", "threat_evolution"]
    present_analytics = [field for field in analytics_fields if field in behavior_insights]
    print(f"Behavior insights contains these analytics: {', '.join(present_analytics)}")
    
    # Verify trend analysis if present
    if "trend_analysis" in behavior_insights:
        trends = behavior_insights["trend_analysis"]
        assert isinstance(trends, dict), "trend_analysis should be a dict"
        
        trend_fields = ["emerging_threats", "declining_techniques", "seasonal_patterns"]
        present_trends = [field for field in trend_fields if field in trends]
        print(f"Trend analysis contains: {', '.join(present_trends)}")
    
    # Verify anomaly detection if present
    if "anomaly_detection" in behavior_insights:
        anomalies = behavior_insights["anomaly_detection"]
        assert isinstance(anomalies, list), "anomaly_detection should be a list"
        
        for anomaly in anomalies[:3]:  # Check first 3 anomalies
            if isinstance(anomaly, dict):
                assert "anomaly_type" in anomaly, "Each anomaly should have an 'anomaly_type'"
                assert "severity" in anomaly, "Each anomaly should have a 'severity'"
    
    # Check for deception-specific insights
    deception_fields = ["honeypot_interactions", "decoy_effectiveness", "attacker_confusion_metrics"]
    present_deception = [field for field in deception_fields if field in behavior_insights]
    print(f"Deception-specific insights: {', '.join(present_deception)}")
    
    # Verify honeypot interactions if present
    if "honeypot_interactions" in behavior_insights:
        interactions = behavior_insights["honeypot_interactions"]
        assert isinstance(interactions, dict), "honeypot_interactions should be a dict"
        
        interaction_fields = ["total_interactions", "unique_attackers", "interaction_duration", "most_targeted_decoys"]
        present_interactions = [field for field in interaction_fields if field in interactions]
        print(f"Honeypot interaction metrics: {', '.join(present_interactions)}")
    
    # Log comprehensive behavior insights summary
    print(f"Behavior insights summary:")
    print(f"  - Attacker profiles: {len(attacker_profiles)}")
    print(f"  - Behavioral patterns: {len(behavioral_patterns)}")
    print(f"  - Attack methodology categories: {len(present_methodologies)}")
    print(f"  - Advanced analytics: {len(present_analytics)}")
    print(f"  - Deception insights: {len(present_deception)}")
    
    # Verify data freshness if timestamp available
    if "last_updated" in behavior_insights:
        print(f"  - Data last updated: {behavior_insights['last_updated']}")
    
    if "analysis_period" in behavior_insights:
        period = behavior_insights["analysis_period"]
        print(f"  - Analysis period: {period}")

    print(f"Successfully retrieved and validated Acalvio attacker behavior insights")

    return True