# 6-test_threat_analytics.py

async def test_threat_analytics(zerg_state=None):
    """Test Team Cymru cyber threat analytics generation"""
    print("Attempting to generate threat analytics using Team Cymru connector")

    assert zerg_state, "this test requires valid zerg_state"

    teamcymru_api_key = zerg_state.get("teamcymru_api_key").get("value")
    teamcymru_api_secret = zerg_state.get("teamcymru_api_secret").get("value")
    teamcymru_username = zerg_state.get("teamcymru_username").get("value")

    from connectors.teamcymru.config import TeamCymruConnectorConfig
    from connectors.teamcymru.connector import TeamCymruConnector
    from connectors.teamcymru.tools import TeamCymruConnectorTools, GenerateThreatAnalyticsInput
    from connectors.teamcymru.target import TeamCymruTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = TeamCymruConnectorConfig(
        api_key=teamcymru_api_key,
        api_secret=teamcymru_api_secret,
        username=teamcymru_username
    )
    assert isinstance(config, ConnectorConfig), "TeamCymruConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = TeamCymruConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TeamCymruConnector should be of type Connector"

    # get query target options for feed sources
    teamcymru_query_target_options = await connector.get_query_target_options()
    assert isinstance(teamcymru_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select feed sources to target
    feed_source_selector = None
    for selector in teamcymru_query_target_options.selectors:
        if selector.type == 'feed_source_ids':  
            feed_source_selector = selector
            break

    assert feed_source_selector, "failed to retrieve feed source selector from query target options"

    assert isinstance(feed_source_selector.values, list), "feed_source_selector values must be a list"
    feed_source_id = feed_source_selector.values[0] if feed_source_selector.values else None
    print(f"Selecting feed source ID: {feed_source_id}")

    assert feed_source_id, f"failed to retrieve feed source ID from feed source selector"

    # set up the target with feed source ID
    target = TeamCymruTarget(feed_source_ids=[feed_source_id])
    assert isinstance(target, ConnectorTargetInterface), "TeamCymruTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the generate_threat_analytics tool
    generate_threat_analytics_tool = next(tool for tool in tools if tool.name == "generate_threat_analytics")
    
    # Test threat analytics generation
    threat_analytics_result = await generate_threat_analytics_tool.execute(
        feed_source_id=feed_source_id,
        time_period="24h",
        include_enrichment=True
    )
    threat_analytics = threat_analytics_result.result

    print("Type of returned threat analytics:", type(threat_analytics))
    print(f"Threat analytics data: {str(threat_analytics)[:300]}")

    # Verify that threat_analytics is a dictionary with expected structure
    assert isinstance(threat_analytics, dict), "threat_analytics should be a dictionary"
    
    # Verify essential threat analytics fields
    assert "threat_summary" in threat_analytics, "Threat analytics should have a 'threat_summary' field"
    assert "indicator_analysis" in threat_analytics, "Threat analytics should have an 'indicator_analysis' field"
    assert "geographic_distribution" in threat_analytics, "Threat analytics should have a 'geographic_distribution' field"
    
    # Verify threat summary structure
    threat_summary = threat_analytics["threat_summary"]
    assert isinstance(threat_summary, dict), "threat_summary should be a dictionary"
    
    summary_fields = ["total_indicators", "malware_families", "threat_types"]
    present_summary_fields = [field for field in summary_fields if field in threat_summary]
    
    print(f"Threat summary contains: {', '.join(present_summary_fields)}")
    
    # Verify indicator analysis if present
    indicator_analysis = threat_analytics["indicator_analysis"]
    assert isinstance(indicator_analysis, dict), "indicator_analysis should be a dictionary"
    
    analysis_fields = ["ip_indicators", "domain_indicators", "hash_indicators"]
    present_analysis_fields = [field for field in analysis_fields if field in indicator_analysis]
    
    print(f"Indicator analysis contains: {', '.join(present_analysis_fields)}")
    
    # Test malware family analysis if available
    if "get_malware_families" in [tool.name for tool in tools]:
        get_malware_families_tool = next(tool for tool in tools if tool.name == "get_malware_families")
        malware_families_result = await get_malware_families_tool.execute(
            feed_source_id=feed_source_id
        )
        malware_families = malware_families_result.result
        
        if malware_families:
            assert isinstance(malware_families, list), "Malware families should be a list"
            
            if len(malware_families) > 0:
                first_family = malware_families[0]
                assert "name" in first_family, "Each malware family should have name"
                
                print(f"Found {len(malware_families)} malware families")
    
    # Test campaign analysis if available
    if "get_campaign_analysis" in [tool.name for tool in tools]:
        get_campaign_analysis_tool = next(tool for tool in tools if tool.name == "get_campaign_analysis")
        campaign_analysis_result = await get_campaign_analysis_tool.execute(
            feed_source_id=feed_source_id,
            time_period="7d"
        )
        campaign_analysis = campaign_analysis_result.result
        
        if campaign_analysis:
            assert isinstance(campaign_analysis, dict), "Campaign analysis should be a dictionary"
            
            campaign_fields = ["active_campaigns", "campaign_trends", "attribution"]
            present_campaign_fields = [field for field in campaign_fields if field in campaign_analysis]
            
            print(f"Campaign analysis contains: {', '.join(present_campaign_fields)}")

    print(f"Successfully generated comprehensive threat analytics")

    return True