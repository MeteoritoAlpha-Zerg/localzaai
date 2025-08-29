# 6-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Revelstoke SOAR threat intelligence and security artifacts retrieval"""
    print("Attempting to retrieve threat intelligence using Revelstoke SOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    revelstoke_url = zerg_state.get("revelstoke_url").get("value")
    revelstoke_api_key = zerg_state.get("revelstoke_api_key", {}).get("value")
    revelstoke_username = zerg_state.get("revelstoke_username", {}).get("value")
    revelstoke_password = zerg_state.get("revelstoke_password", {}).get("value")
    revelstoke_tenant_id = zerg_state.get("revelstoke_tenant_id", {}).get("value")

    from connectors.revelstoke.config import RevelstokeSoarConnectorConfig
    from connectors.revelstoke.connector import RevelstokeSoarConnector
    from connectors.revelstoke.tools import RevelstokeSoarConnectorTools
    from connectors.revelstoke.target import RevelstokeSoarTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # prefer API key over username/password
    if revelstoke_api_key:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            api_key=revelstoke_api_key,
            tenant_id=revelstoke_tenant_id,
        )
    elif revelstoke_username and revelstoke_password:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            username=revelstoke_username,
            password=revelstoke_password,
            tenant_id=revelstoke_tenant_id,
        )
    else:
        raise Exception("Either revelstoke_api_key or both revelstoke_username and revelstoke_password must be provided")

    assert isinstance(config, ConnectorConfig), "RevelstokeSoarConnectorConfig should be of type ConnectorConfig"

    connector = RevelstokeSoarConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RevelstokeSoarConnector should be of type Connector"

    revelstoke_query_target_options = await connector.get_query_target_options()
    assert isinstance(revelstoke_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    playbook_selector = None
    for selector in revelstoke_query_target_options.selectors:
        if selector.type == 'playbook_ids':  
            playbook_selector = selector
            break

    assert playbook_selector, "failed to retrieve playbook selector from query target options"

    assert isinstance(playbook_selector.values, list), "playbook_selector values must be a list"
    playbook_id = playbook_selector.values[0] if playbook_selector.values else None
    print(f"Selecting playbook ID: {playbook_id}")

    assert playbook_id, f"failed to retrieve playbook ID from playbook selector"

    target = RevelstokeSoarTarget(playbook_ids=[playbook_id])
    assert isinstance(target, ConnectorTargetInterface), "RevelstokeSoarTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get threat intelligence indicators
    get_revelstoke_indicators_tool = next(tool for tool in tools if tool.name == "get_revelstoke_indicators")
    revelstoke_indicators_result = await get_revelstoke_indicators_tool.execute(limit=15)
    revelstoke_indicators = revelstoke_indicators_result.result

    print("Type of returned revelstoke_indicators:", type(revelstoke_indicators))
    print(f"len indicators: {len(revelstoke_indicators)} indicators: {str(revelstoke_indicators)[:200]}")

    assert isinstance(revelstoke_indicators, list), "revelstoke_indicators should be a list"
    
    if len(revelstoke_indicators) > 0:
        indicators_to_check = revelstoke_indicators[:3] if len(revelstoke_indicators) > 3 else revelstoke_indicators
        
        for indicator in indicators_to_check:
            assert "id" in indicator, "Each indicator should have an 'id' field"
            assert "type" in indicator, "Each indicator should have a 'type' field"
            assert "value" in indicator, "Each indicator should have a 'value' field"
            
            valid_indicator_types = ["ip", "domain", "url", "file_hash", "email", "registry_key", "mutex"]
            assert indicator["type"] in valid_indicator_types, f"Indicator type {indicator['type']} is not valid"
            
            indicator_fields = ["confidence", "threat_score", "tags", "source", "first_seen", "last_seen"]
            present_indicator_fields = [field for field in indicator_fields if field in indicator]
            
            print(f"Indicator {indicator['value']} ({indicator['type']}) contains these fields: {', '.join(present_indicator_fields)}")

        print(f"Successfully retrieved and validated {len(revelstoke_indicators)} Revelstoke SOAR indicators")

    # Test 2: Get security artifacts
    get_revelstoke_artifacts_tool = next(tool for tool in tools if tool.name == "get_revelstoke_artifacts")
    revelstoke_artifacts_result = await get_revelstoke_artifacts_tool.execute(limit=10)
    revelstoke_artifacts = revelstoke_artifacts_result.result

    print("Type of returned revelstoke_artifacts:", type(revelstoke_artifacts))

    assert isinstance(revelstoke_artifacts, list), "revelstoke_artifacts should be a list"
    
    if len(revelstoke_artifacts) > 0:
        artifacts_to_check = revelstoke_artifacts[:3] if len(revelstoke_artifacts) > 3 else revelstoke_artifacts
        
        for artifact in artifacts_to_check:
            assert "id" in artifact, "Each artifact should have an 'id' field"
            assert "name" in artifact, "Each artifact should have a 'name' field"
            assert "type" in artifact, "Each artifact should have a 'type' field"
            
            valid_artifact_types = ["file", "network_capture", "memory_dump", "log_file", "screenshot", "report"]
            
            artifact_fields = ["size", "hash", "mime_type", "created_at", "case_id", "tags"]
            present_artifact_fields = [field for field in artifact_fields if field in artifact]
            
            print(f"Artifact {artifact['name']} ({artifact['type']}) contains these fields: {', '.join(present_artifact_fields)}")

        print(f"Successfully retrieved and validated {len(revelstoke_artifacts)} Revelstoke SOAR artifacts")

    # Test 3: Get enrichment data
    get_revelstoke_enrichment_tool = next(tool for tool in tools if tool.name == "get_revelstoke_enrichment")
    
    test_indicator = "8.8.8.8"  # Use a common IP for testing
    
    revelstoke_enrichment_result = await get_revelstoke_enrichment_tool.execute(
        indicator_value=test_indicator,
        indicator_type="ip"
    )
    revelstoke_enrichment = revelstoke_enrichment_result.result

    print("Type of returned revelstoke_enrichment:", type(revelstoke_enrichment))

    assert isinstance(revelstoke_enrichment, dict), "revelstoke_enrichment should be a dictionary"
    
    if revelstoke_enrichment:
        assert "indicator" in revelstoke_enrichment, "Enrichment should contain indicator field"
        assert "reputation" in revelstoke_enrichment, "Enrichment should contain reputation field"
        
        enrichment_fields = ["geo_location", "asn", "reputation_score", "threat_categories", "sources"]
        present_enrichment_fields = [field for field in enrichment_fields if field in revelstoke_enrichment]
        
        print(f"Enrichment for {test_indicator} contains these fields: {', '.join(present_enrichment_fields)}")

    # Test 4: Get threat feeds
    get_revelstoke_feeds_tool = next(tool for tool in tools if tool.name == "get_revelstoke_feeds")
    revelstoke_feeds_result = await get_revelstoke_feeds_tool.execute()
    revelstoke_feeds = revelstoke_feeds_result.result

    print("Type of returned revelstoke_feeds:", type(revelstoke_feeds))

    assert isinstance(revelstoke_feeds, list), "revelstoke_feeds should be a list"
    
    if len(revelstoke_feeds) > 0:
        feeds_to_check = revelstoke_feeds[:3] if len(revelstoke_feeds) > 3 else revelstoke_feeds
        
        for feed in feeds_to_check:
            assert "id" in feed, "Each feed should have an 'id' field"
            assert "name" in feed, "Each feed should have a 'name' field"
            assert "enabled" in feed, "Each feed should have an 'enabled' field"
            
            feed_fields = ["source", "feed_type", "last_updated", "indicator_count", "confidence"]
            present_feed_fields = [field for field in feed_fields if field in feed]
            
            print(f"Threat feed {feed['name']} contains these fields: {', '.join(present_feed_fields)}")

        print(f"Successfully retrieved and validated {len(revelstoke_feeds)} Revelstoke SOAR threat feeds")

    print("Successfully completed threat intelligence and security artifacts tests")

    return True