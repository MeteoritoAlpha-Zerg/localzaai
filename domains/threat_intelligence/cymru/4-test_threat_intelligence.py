# 4-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Team Cymru threat intelligence enumeration by way of connector tools"""
    print("Attempting to retrieve Team Cymru threat intelligence using Team Cymru connector")

    assert zerg_state, "this test requires valid zerg_state"

    teamcymru_api_key = zerg_state.get("teamcymru_api_key").get("value")
    teamcymru_api_secret = zerg_state.get("teamcymru_api_secret").get("value")
    teamcymru_username = zerg_state.get("teamcymru_username").get("value")

    from connectors.teamcymru.config import TeamCymruConnectorConfig
    from connectors.teamcymru.connector import TeamCymruConnector
    from connectors.teamcymru.tools import TeamCymruConnectorTools
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

    # get query target options
    teamcymru_query_target_options = await connector.get_query_target_options()
    assert isinstance(teamcymru_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select feed sources to target
    feed_source_selector = None
    for selector in teamcymru_query_target_options.selectors:
        if selector.type == 'feed_source_ids':  
            feed_source_selector = selector
            break

    assert feed_source_selector, "failed to retrieve feed source selector from query target options"

    # grab the first two feed sources 
    num_feeds = 2
    assert isinstance(feed_source_selector.values, list), "feed_source_selector values must be a list"
    feed_source_ids = feed_source_selector.values[:num_feeds] if feed_source_selector.values else None
    print(f"Selecting feed source IDs: {feed_source_ids}")

    assert feed_source_ids, f"failed to retrieve {num_feeds} feed source IDs from feed source selector"

    # set up the target with feed source IDs
    target = TeamCymruTarget(feed_source_ids=feed_source_ids)
    assert isinstance(target, ConnectorTargetInterface), "TeamCymruTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_teamcymru_threat_intel tool
    teamcymru_get_threat_intel_tool = next(tool for tool in tools if tool.name == "get_teamcymru_threat_intel")
    teamcymru_threat_intel_result = await teamcymru_get_threat_intel_tool.execute()
    teamcymru_threat_intel = teamcymru_threat_intel_result.result

    print("Type of returned teamcymru_threat_intel:", type(teamcymru_threat_intel))
    print(f"len threat intel: {len(teamcymru_threat_intel)} intel: {str(teamcymru_threat_intel)[:200]}")

    # Verify that teamcymru_threat_intel is a list
    assert isinstance(teamcymru_threat_intel, list), "teamcymru_threat_intel should be a list"
    assert len(teamcymru_threat_intel) > 0, "teamcymru_threat_intel should not be empty"
    
    # Verify structure of each threat intelligence object
    for intel in teamcymru_threat_intel:
        assert "indicator" in intel, "Each threat intel should have an 'indicator' field"
        assert "indicator_type" in intel, "Each threat intel should have an 'indicator_type' field"
        assert "threat_type" in intel, "Each threat intel should have a 'threat_type' field"
        
        # Verify essential Team Cymru threat intel fields
        assert "first_seen" in intel, "Each threat intel should have a 'first_seen' field"
        assert "confidence" in intel, "Each threat intel should have a 'confidence' field"
        assert "tags" in intel, "Each threat intel should have a 'tags' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["malware_family", "campaign", "country", "asn"]
        present_fields = [field for field in descriptive_fields if field in intel]
        
        print(f"Threat intel {intel['indicator']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first threat intel
        if intel == teamcymru_threat_intel[0]:
            print(f"Example threat intel structure: {intel}")

    print(f"Successfully retrieved and validated {len(teamcymru_threat_intel)} Team Cymru threat intelligence records")

    return True