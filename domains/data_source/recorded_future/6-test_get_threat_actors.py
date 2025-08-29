# 6-test_get_threat_actors.py

async def test_get_threat_actors(zerg_state=None):
    """Test Recorded Future threat actor intelligence retrieval"""
    print("Testing Recorded Future threat actor intelligence retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    rf_api_url = zerg_state.get("recorded_future_api_url").get("value")
    rf_api_token = zerg_state.get("recorded_future_api_token").get("value")

    from connectors.recorded_future.config import RecordedFutureConnectorConfig
    from connectors.recorded_future.connector import RecordedFutureConnector
    from connectors.recorded_future.target import RecordedFutureTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = RecordedFutureConnectorConfig(
        api_url=rf_api_url,
        api_token=rf_api_token
    )
    assert isinstance(config, ConnectorConfig), "RecordedFutureConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = RecordedFutureConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RecordedFutureConnector should be of type Connector"

    # get query target options
    rf_query_target_options = await connector.get_query_target_options()
    assert isinstance(rf_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select threat actors intelligence source
    intelligence_source_selector = None
    for selector in rf_query_target_options.selectors:
        if selector.type == 'intelligence_sources':  
            intelligence_source_selector = selector
            break

    assert intelligence_source_selector, "failed to retrieve intelligence source selector from query target options"
    assert isinstance(intelligence_source_selector.values, list), "intelligence_source_selector values must be a list"
    
    # Find threat actors in available intelligence sources
    threat_actors_source = None
    for source in intelligence_source_selector.values:
        if 'threat' in source.lower() and 'actor' in source.lower():
            threat_actors_source = source
            break
    
    assert threat_actors_source, "Threat actors intelligence source not found in available options"
    print(f"Selecting threat actors intelligence source: {threat_actors_source}")

    # set up the target with threat actors intelligence source
    target = RecordedFutureTarget(intelligence_sources=[threat_actors_source])
    assert isinstance(target, ConnectorTargetInterface), "RecordedFutureTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_recorded_future_threat_actors tool and execute it
    get_rf_threat_actors_tool = next(tool for tool in tools if tool.name == "get_recorded_future_threat_actors")
    threat_actors_result = await get_rf_threat_actors_tool.execute()
    threat_actors_data = threat_actors_result.result

    print("Type of returned threat actors data:", type(threat_actors_data))
    print(f"Threat actors count: {len(threat_actors_data)} sample: {str(threat_actors_data)[:200]}")

    # Verify that threat_actors_data is a list
    assert isinstance(threat_actors_data, list), "Threat actors data should be a list"
    assert len(threat_actors_data) > 0, "Threat actors data should not be empty"
    
    # Limit the number of threat actors to check if there are many
    actors_to_check = threat_actors_data[:3] if len(threat_actors_data) > 3 else threat_actors_data
    
    # Verify structure of each threat actor entry
    for actor in actors_to_check:
        # Verify essential threat actor fields
        assert "entity" in actor, "Each threat actor should have an 'entity' field"
        assert "risk" in actor, "Each threat actor should have a 'risk' field"
        
        # Verify entity structure
        entity = actor["entity"]
        assert "id" in entity, "Entity should have an 'id' field"
        assert "name" in entity, "Entity should have a 'name' field"
        assert "type" in entity, "Entity should have a 'type' field"
        
        # Verify entity type is threat actor related
        entity_type = entity["type"].lower()
        assert "threat" in entity_type or "actor" in entity_type or "malware" in entity_type, f"Entity type should be threat actor related: {entity_type}"
        
        # Verify risk structure
        risk = actor["risk"]
        assert "score" in risk, "Risk should have a 'score' field"
        assert isinstance(risk["score"], (int, float)), "Risk score should be numeric"
        assert 0 <= risk["score"] <= 100, "Risk score should be between 0 and 100"
        
        # Check for threat actor specific fields
        actor_fields = ["aliases", "targets", "operations", "ttps", "indicators"]
        present_fields = [field for field in actor_fields if field in actor]
        
        print(f"Threat actor {entity['name']} (risk: {risk['score']}) contains: {', '.join(present_fields)}")
        
        # Verify actor name is not empty
        assert entity["name"].strip(), "Threat actor name should not be empty"
        
        # Log the structure of the first threat actor for debugging
        if actor == actors_to_check[0]:
            print(f"Example threat actor structure: {actor}")

    print(f"Successfully retrieved and validated {len(threat_actors_data)} Recorded Future threat actors")

    return True