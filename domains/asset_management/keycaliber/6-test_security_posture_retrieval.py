# 6-test_security_posture_retrieval.py

async def test_security_posture_retrieval(zerg_state=None):
    """Test Key Caliber security posture retrieval by way of connector tools"""
    print("Retrieving security posture scores using Key Caliber connector")

    assert zerg_state, "this test requires valid zerg_state"

    keycaliber_host = zerg_state.get("keycaliber_host").get("value")
    keycaliber_api_key = zerg_state.get("keycaliber_api_key").get("value")

    from connectors.keycaliber.config import KeyCaliberConnectorConfig
    from connectors.keycaliber.connector import KeyCaliberConnector
    from connectors.keycaliber.tools import KeyCaliberConnectorTools, GetKeyCaliberSecurityPostureInput
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

    # set up the target (security posture queries typically cover organizational scope)
    target = KeyCaliberTarget()
    assert isinstance(target, ConnectorTargetInterface), "KeyCaliberTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_security_posture tool and execute it
    get_security_posture_tool = next(tool for tool in tools if tool.name == "get_security_posture")
    security_posture_result = await get_security_posture_tool.execute()
    security_posture = security_posture_result.result

    print("Type of returned security_posture:", type(security_posture))
    print(f"len posture scores: {len(security_posture)} scores: {str(security_posture)[:200]}")

    # Verify that security_posture is a list
    assert isinstance(security_posture, list), "security_posture should be a list"
    assert len(security_posture) > 0, "security_posture should not be empty"
    
    # Limit the number of posture scores to check if there are many
    posture_scores_to_check = security_posture[:5] if len(security_posture) > 5 else security_posture
    
    # Verify structure of each security posture score object
    for posture_score in posture_scores_to_check:
        # Verify essential Key Caliber security posture fields
        assert "asset_id" in posture_score, "Each posture score should have an 'asset_id' field"
        assert "overall_score" in posture_score, "Each posture score should have an 'overall_score' field"
        
        # Check for additional descriptive fields (common in Key Caliber security posture assessments)
        optional_fields = ["asset_name", "asset_type", "vulnerability_score", "patch_management_score", "configuration_score", "access_control_score", "monitoring_score", "incident_response_score", "compliance_score", "threat_intelligence_score", "risk_level", "security_controls", "last_assessment", "next_assessment", "assessment_methodology", "assessor", "recommendations", "remediation_priority"]
        present_optional = [field for field in optional_fields if field in posture_score]
        
        print(f"Posture score {posture_score['asset_id']} ({posture_score.get('asset_name', 'Unknown')}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first posture score for debugging
        if posture_score == posture_scores_to_check[0]:
            print(f"Example security posture structure: {posture_score}")

    # Display information about some security posture scores
    for i, posture_score in enumerate(posture_scores_to_check[:3]):
        print(f"Security Posture {i+1}:")
        print(f"  Asset ID: {posture_score.get('asset_id')}")
        print(f"  Asset Name: {posture_score.get('asset_name', 'Unknown')}")
        print(f"  Overall Score: {posture_score.get('overall_score')}")
        print(f"  Risk Level: {posture_score.get('risk_level', 'Not specified')}")

    # Analyze security posture distribution
    risk_levels = {}
    overall_scores = []
    for posture_score in security_posture:
        risk_level = posture_score.get('risk_level', 'Unknown')
        if risk_level not in risk_levels:
            risk_levels[risk_level] = 0
        risk_levels[risk_level] += 1
        
        if 'overall_score' in posture_score:
            overall_scores.append(posture_score['overall_score'])

    print("Security posture distribution by risk level:")
    for risk_level, count in risk_levels.items():
        print(f"  {risk_level}: {count}")

    if overall_scores:
        avg_score = sum(overall_scores) / len(overall_scores)
        print(f"Average overall security score: {avg_score:.2f}")

    # Check for critical security findings
    critical_assets = [score for score in security_posture if score.get('risk_level') == 'Critical' or score.get('overall_score', 100) < 30]
    if critical_assets:
        print(f"Found {len(critical_assets)} assets with critical security posture issues")
        for critical in critical_assets[:3]:  # Show first 3 critical assets
            print(f"  Critical Asset: {critical.get('asset_id')} - Score: {critical.get('overall_score')}")

    print(f"Successfully retrieved and validated {len(security_posture)} Key Caliber security posture scores")

    return True