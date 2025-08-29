# 4-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Dragos OT threat intelligence retrieval by way of connector tools"""
    print("Attempting to authenticate using Dragos connector")

    assert zerg_state, "this test requires valid zerg_state"

    dragos_api_url = zerg_state.get("dragos_api_url").get("value")
    dragos_api_key = zerg_state.get("dragos_api_key").get("value")
    dragos_api_secret = zerg_state.get("dragos_api_secret").get("value")
    dragos_client_id = zerg_state.get("dragos_client_id").get("value")
    dragos_api_version = zerg_state.get("dragos_api_version").get("value")

    from connectors.dragos.config import DragosConnectorConfig
    from connectors.dragos.connector import DragosConnector
    from connectors.dragos.tools import DragosConnectorTools
    from connectors.dragos.target import DragosTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = DragosConnectorConfig(
        api_url=dragos_api_url,
        api_key=dragos_api_key,
        api_secret=dragos_api_secret,
        client_id=dragos_client_id,
        api_version=dragos_api_version
    )
    assert isinstance(config, ConnectorConfig), "DragosConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = DragosConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DragosConnector should be of type Connector"

    # get query target options
    dragos_query_target_options = await connector.get_query_target_options()
    assert isinstance(dragos_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select threat intelligence feeds to target
    threat_feed_selector = None
    for selector in dragos_query_target_options.selectors:
        if selector.type == 'threat_intelligence_feeds':  
            threat_feed_selector = selector
            break

    assert threat_feed_selector, "failed to retrieve threat intelligence feed selector from query target options"

    # grab the first two threat intelligence feeds 
    num_feeds = 2
    assert isinstance(threat_feed_selector.values, list), "threat_feed_selector values must be a list"
    threat_feeds = threat_feed_selector.values[:num_feeds] if threat_feed_selector.values else None
    print(f"Selecting threat intelligence feeds: {threat_feeds}")

    assert threat_feeds, f"failed to retrieve {num_feeds} threat intelligence feeds from feed selector"

    # set up the target with threat intelligence feeds
    target = DragosTarget(threat_intelligence_feeds=threat_feeds)
    assert isinstance(target, ConnectorTargetInterface), "DragosTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_dragos_threat_intelligence tool
    dragos_get_threat_intel_tool = next(tool for tool in tools if tool.name == "get_dragos_threat_intelligence")
    dragos_threat_intel_result = await dragos_get_threat_intel_tool.execute()
    dragos_threat_intel = dragos_threat_intel_result.result

    print("Type of returned dragos_threat_intel:", type(dragos_threat_intel))
    print(f"len threat intel: {len(dragos_threat_intel)} threat intel: {str(dragos_threat_intel)[:200]}")

    # ensure that dragos_threat_intel are a list of objects with OT threat intelligence information
    # and the object having the threat data and analysis from the dragos specification
    # as may be descriptive
    # Verify that dragos_threat_intel is a list
    assert isinstance(dragos_threat_intel, list), "dragos_threat_intel should be a list"
    assert len(dragos_threat_intel) > 0, "dragos_threat_intel should not be empty"
    assert len(dragos_threat_intel) <= 100, f"dragos_threat_intel should have reasonable number of entries"
    
    # Limit the number of threat intel items to check if there are many
    threat_intel_to_check = dragos_threat_intel[:5] if len(dragos_threat_intel) > 5 else dragos_threat_intel
    
    # Verify structure of each threat intelligence object
    for threat_intel in threat_intel_to_check:
        assert "id" in threat_intel, "Each threat intelligence item should have an 'id' field"
        assert "title" in threat_intel, "Each threat intelligence item should have a 'title' field"
        
        # Verify essential OT threat intelligence fields
        # These are common fields in Dragos threat intelligence based on OT security specifications
        assert "activity_group" in threat_intel, "Each threat intelligence item should have an 'activity_group' field"
        assert "threat_type" in threat_intel, "Each threat intelligence item should have a 'threat_type' field"
        
        # Check that threat intelligence feed is one of the requested feeds
        if "feed_source" in threat_intel:
            assert threat_intel["feed_source"] in threat_feeds, f"Feed source {threat_intel['feed_source']} is not in the requested threat_feeds"
        
        # Check for additional essential OT threat intelligence fields
        essential_fields = ["severity", "confidence_level", "first_observed", "last_updated"]
        present_essential = [field for field in essential_fields if field in threat_intel]
        print(f"Threat intel {threat_intel['title']} contains these essential fields: {', '.join(present_essential)}")
        
        # Verify severity level
        if "severity" in threat_intel:
            severity = threat_intel["severity"]
            valid_severities = ["Low", "Medium", "High", "Critical", "Unknown"]
            assert severity in valid_severities, f"Severity {severity} should be one of {valid_severities}"
        
        # Check for TTPs (Tactics, Techniques, Procedures)
        ttp_fields = ["tactics", "techniques", "procedures", "mitre_attack_ids"]
        present_ttps = [field for field in ttp_fields if field in threat_intel]
        print(f"Threat intel {threat_intel['title']} contains these TTP fields: {', '.join(present_ttps)}")
        
        # Check for IOCs (Indicators of Compromise)
        ioc_fields = ["indicators", "file_hashes", "ip_addresses", "domains", "network_signatures"]
        present_iocs = [field for field in ioc_fields if field in threat_intel]
        print(f"Threat intel {threat_intel['title']} contains these IOC fields: {', '.join(present_iocs)}")
        
        # Validate indicators structure if present
        if "indicators" in threat_intel:
            indicators = threat_intel["indicators"]
            assert isinstance(indicators, list), "Indicators should be a list"
            
            for indicator in indicators[:2]:  # Check first 2 indicators
                indicator_fields = ["type", "value", "confidence", "context"]
                present_indicator_fields = [field for field in indicator_fields if field in indicator]
                print(f"Indicator contains: {', '.join(present_indicator_fields)}")
        
        # Check for target information and impact analysis
        target_fields = ["target_industries", "target_systems", "impact_assessment", "affected_protocols"]
        present_targets = [field for field in target_fields if field in threat_intel]
        print(f"Threat intel {threat_intel['title']} contains these target fields: {', '.join(present_targets)}")
        
        # Check for attribution and actor information
        attribution_fields = ["attribution", "actor_motivation", "campaign_name", "associated_malware"]
        present_attribution = [field for field in attribution_fields if field in threat_intel]
        print(f"Threat intel {threat_intel['title']} contains these attribution fields: {', '.join(present_attribution)}")
        
        # Check for technical analysis and context
        analysis_fields = ["technical_analysis", "kill_chain_phase", "detection_methods", "countermeasures"]
        present_analysis = [field for field in analysis_fields if field in threat_intel]
        print(f"Threat intel {threat_intel['title']} contains these analysis fields: {', '.join(present_analysis)}")
        
        # Check for OT-specific context
        ot_fields = ["ot_protocols", "ics_components", "scada_systems", "safety_impact"]
        present_ot = [field for field in ot_fields if field in threat_intel]
        print(f"Threat intel {threat_intel['title']} contains these OT fields: {', '.join(present_ot)}")
        
        # Log the full structure of the first threat intelligence item
        if threat_intel == threat_intel_to_check[0]:
            print(f"Example threat intelligence structure: {threat_intel}")

    print(f"Successfully retrieved and validated {len(dragos_threat_intel)} Dragos OT threat intelligence items")

    return True