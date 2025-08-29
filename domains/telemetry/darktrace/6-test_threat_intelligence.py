# 6-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Darktrace threat intelligence and cyber events retrieval"""
    print("Attempting to retrieve threat intelligence using Darktrace connector")

    assert zerg_state, "this test requires valid zerg_state"

    darktrace_url = zerg_state.get("darktrace_url").get("value")
    darktrace_public_token = zerg_state.get("darktrace_public_token").get("value")
    darktrace_private_token = zerg_state.get("darktrace_private_token").get("value")

    from connectors.darktrace.config import DarktraceConnectorConfig
    from connectors.darktrace.connector import DarktraceConnector
    from connectors.darktrace.tools import DarktraceConnectorTools
    from connectors.darktrace.target import DarktraceTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = DarktraceConnectorConfig(
        url=darktrace_url,
        public_token=darktrace_public_token,
        private_token=darktrace_private_token,
    )
    assert isinstance(config, ConnectorConfig), "DarktraceConnectorConfig should be of type ConnectorConfig"

    connector = DarktraceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DarktraceConnector should be of type Connector"

    darktrace_query_target_options = await connector.get_query_target_options()
    assert isinstance(darktrace_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    model_selector = None
    for selector in darktrace_query_target_options.selectors:
        if selector.type == 'model_uuids':  
            model_selector = selector
            break

    assert model_selector, "failed to retrieve model selector from query target options"

    assert isinstance(model_selector.values, list), "model_selector values must be a list"
    model_uuid = model_selector.values[0] if model_selector.values else None
    print(f"Selecting model UUID: {model_uuid}")

    assert model_uuid, f"failed to retrieve model UUID from model selector"

    target = DarktraceTarget(model_uuids=[model_uuid])
    assert isinstance(target, ConnectorTargetInterface), "DarktraceTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get threat intelligence feeds
    get_darktrace_threat_feeds_tool = next(tool for tool in tools if tool.name == "get_darktrace_threat_feeds")
    darktrace_threat_feeds_result = await get_darktrace_threat_feeds_tool.execute()
    darktrace_threat_feeds = darktrace_threat_feeds_result.result

    print("Type of returned darktrace_threat_feeds:", type(darktrace_threat_feeds))

    assert isinstance(darktrace_threat_feeds, list), "darktrace_threat_feeds should be a list"
    
    if len(darktrace_threat_feeds) > 0:
        feeds_to_check = darktrace_threat_feeds[:3] if len(darktrace_threat_feeds) > 3 else darktrace_threat_feeds
        
        for feed in feeds_to_check:
            assert "id" in feed, "Each threat feed should have an 'id' field"
            assert "name" in feed, "Each threat feed should have a 'name' field"
            assert "enabled" in feed, "Each threat feed should have an 'enabled' field"
            
            feed_fields = ["description", "feedType", "lastUpdated", "source", "indicatorCount"]
            present_feed_fields = [field for field in feed_fields if field in feed]
            
            print(f"Threat feed {feed['name']} contains these fields: {', '.join(present_feed_fields)}")

        print(f"Successfully retrieved and validated {len(darktrace_threat_feeds)} Darktrace threat feeds")

    # Test 2: Get Antigena actions
    get_darktrace_antigena_tool = next(tool for tool in tools if tool.name == "get_darktrace_antigena")
    darktrace_antigena_result = await get_darktrace_antigena_tool.execute(limit=10)
    darktrace_antigena = darktrace_antigena_result.result

    print("Type of returned darktrace_antigena:", type(darktrace_antigena))

    assert isinstance(darktrace_antigena, list), "darktrace_antigena should be a list"
    
    if len(darktrace_antigena) > 0:
        antigena_to_check = darktrace_antigena[:3] if len(darktrace_antigena) > 3 else darktrace_antigena
        
        for action in antigena_to_check:
            assert "aaid" in action, "Each Antigena action should have an 'aaid' field"
            assert "device" in action, "Each Antigena action should have a 'device' field"
            assert "trigger" in action, "Each Antigena action should have a 'trigger' field"
            assert "action" in action, "Each Antigena action should have an 'action' field"
            
            action_fields = ["timestamp", "inhibitor", "actionTaken", "description", "pid"]
            present_action_fields = [field for field in action_fields if field in action]
            
            print(f"Antigena action {action['aaid']} contains these fields: {', '.join(present_action_fields)}")

        print(f"Successfully retrieved and validated {len(darktrace_antigena)} Darktrace Antigena actions")

    # Test 3: Get system status and health
    get_darktrace_status_tool = next(tool for tool in tools if tool.name == "get_darktrace_status")
    darktrace_status_result = await get_darktrace_status_tool.execute()
    darktrace_status = darktrace_status_result.result

    print("Type of returned darktrace_status:", type(darktrace_status))

    assert isinstance(darktrace_status, dict), "darktrace_status should be a dictionary"
    
    if darktrace_status:
        status_fields = ["version", "build", "license", "probeConnections", "uptime", "systemHealth"]
        present_status_fields = [field for field in status_fields if field in darktrace_status]
        
        print(f"System status contains these fields: {', '.join(present_status_fields)}")

    # Test 4: Get tags and labels
    get_darktrace_tags_tool = next(tool for tool in tools if tool.name == "get_darktrace_tags")
    darktrace_tags_result = await get_darktrace_tags_tool.execute()
    darktrace_tags = darktrace_tags_result.result

    print("Type of returned darktrace_tags:", type(darktrace_tags))

    assert isinstance(darktrace_tags, list), "darktrace_tags should be a list"
    
    if len(darktrace_tags) > 0:
        tags_to_check = darktrace_tags[:5] if len(darktrace_tags) > 5 else darktrace_tags
        
        for tag in tags_to_check:
            assert "name" in tag, "Each tag should have a 'name' field"
            
            tag_fields = ["description", "color", "devices", "expiry"]
            present_tag_fields = [field for field in tag_fields if field in tag]
            
            print(f"Tag {tag['name']} contains these fields: {', '.join(present_tag_fields)}")

        print(f"Successfully retrieved and validated {len(darktrace_tags)} Darktrace tags")

    # Test 5: Get threat hunting data
    get_darktrace_hunting_tool = next(tool for tool in tools if tool.name == "get_darktrace_hunting")
    darktrace_hunting_result = await get_darktrace_hunting_tool.execute(
        query="device.ip contains 192.168",
        limit=5
    )
    darktrace_hunting = darktrace_hunting_result.result

    print("Type of returned darktrace_hunting:", type(darktrace_hunting))

    assert isinstance(darktrace_hunting, list), "darktrace_hunting should be a list"
    
    if len(darktrace_hunting) > 0:
        hunting_to_check = darktrace_hunting[:3] if len(darktrace_hunting) > 3 else darktrace_hunting
        
        for result in hunting_to_check:
            # Hunting results structure varies by query type
            assert isinstance(result, dict), "Each hunting result should be a dictionary"
            
            print(f"Hunting result: {str(result)[:100]}")

        print(f"Successfully retrieved and validated {len(darktrace_hunting)} Darktrace hunting results")

    print("Successfully completed threat intelligence and cyber events tests")

    return True