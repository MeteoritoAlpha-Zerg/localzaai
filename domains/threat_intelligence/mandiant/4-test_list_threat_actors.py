# 4-test_list_threat_actors.py

async def test_list_threat_actors(zerg_state=None):
    """Test Mandiant threat actor and campaign enumeration by way of connector tools"""
    print("Attempting to authenticate using Mandiant connector")

    assert zerg_state, "this test requires valid zerg_state"

    mandiant_url = zerg_state.get("mandiant_url").get("value")
    mandiant_api_key = zerg_state.get("mandiant_api_key").get("value")
    mandiant_secret_key = zerg_state.get("mandiant_secret_key").get("value")

    from connectors.mandiant.config import MandiantConnectorConfig
    from connectors.mandiant.connector import MandiantConnector
    from connectors.mandiant.tools import MandiantConnectorTools
    from connectors.mandiant.target import MandiantTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = MandiantConnectorConfig(
        url=mandiant_url,
        api_key=mandiant_api_key,
        secret_key=mandiant_secret_key,
    )
    assert isinstance(config, ConnectorConfig), "MandiantConnectorConfig should be of type ConnectorConfig"

    connector = MandiantConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MandiantConnector should be of type Connector"

    mandiant_query_target_options = await connector.get_query_target_options()
    assert isinstance(mandiant_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    threat_actor_selector = None
    for selector in mandiant_query_target_options.selectors:
        if selector.type == 'threat_actor_ids':  
            threat_actor_selector = selector
            break

    assert threat_actor_selector, "failed to retrieve threat actor selector from query target options"

    num_actors = 2
    assert isinstance(threat_actor_selector.values, list), "threat_actor_selector values must be a list"
    threat_actor_ids = threat_actor_selector.values[:num_actors] if threat_actor_selector.values else None
    print(f"Selecting threat actor IDs: {threat_actor_ids}")

    assert threat_actor_ids, f"failed to retrieve {num_actors} threat actor IDs from threat actor selector"

    target = MandiantTarget(threat_actor_ids=threat_actor_ids)
    assert isinstance(target, ConnectorTargetInterface), "MandiantTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    mandiant_get_threat_actors_tool = next(tool for tool in tools if tool.name == "get_mandiant_threat_actors")
    mandiant_threat_actors_result = await mandiant_get_threat_actors_tool.execute()
    mandiant_threat_actors = mandiant_threat_actors_result.result

    print("Type of returned mandiant_threat_actors:", type(mandiant_threat_actors))
    print(f"len threat actors: {len(mandiant_threat_actors)} actors: {str(mandiant_threat_actors)[:200]}")

    assert isinstance(mandiant_threat_actors, list), "mandiant_threat_actors should be a list"
    assert len(mandiant_threat_actors) > 0, "mandiant_threat_actors should not be empty"
    assert len(mandiant_threat_actors) == num_actors, f"mandiant_threat_actors should have {num_actors} entries"
    
    for actor in mandiant_threat_actors:
        assert "id" in actor, "Each threat actor should have an 'id' field"
        assert actor["id"] in threat_actor_ids, f"Threat actor ID {actor['id']} is not in the requested threat_actor_ids"
        assert "name" in actor, "Each threat actor should have a 'name' field"
        assert "aliases" in actor, "Each threat actor should have an 'aliases' field"
        
        descriptive_fields = ["description", "motivations", "sophistication", "regions", "industries", "last_activity_time"]
        present_fields = [field for field in descriptive_fields if field in actor]
        
        print(f"Threat actor {actor['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        if actor == mandiant_threat_actors[0]:
            print(f"Example threat actor structure: {actor}")

    print(f"Successfully retrieved and validated {len(mandiant_threat_actors)} Mandiant threat actors")

    # Test campaigns as well
    get_mandiant_campaigns_tool = next(tool for tool in tools if tool.name == "get_mandiant_campaigns")
    mandiant_campaigns_result = await get_mandiant_campaigns_tool.execute(limit=10)
    mandiant_campaigns = mandiant_campaigns_result.result

    print("Type of returned mandiant_campaigns:", type(mandiant_campaigns))

    assert isinstance(mandiant_campaigns, list), "mandiant_campaigns should be a list"
    
    if len(mandiant_campaigns) > 0:
        campaigns_to_check = mandiant_campaigns[:3] if len(mandiant_campaigns) > 3 else mandiant_campaigns
        
        for campaign in campaigns_to_check:
            assert "id" in campaign, "Each campaign should have an 'id' field"
            assert "name" in campaign, "Each campaign should have a 'name' field"
            
            campaign_fields = ["description", "first_seen", "last_seen", "attribution", "target_industries"]
            present_campaign_fields = [field for field in campaign_fields if field in campaign]
            
            print(f"Campaign {campaign['name']} contains these fields: {', '.join(present_campaign_fields)}")
        
        print(f"Successfully retrieved and validated {len(mandiant_campaigns)} Mandiant campaigns")

    return True