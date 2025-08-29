# 6-test_threat_attribution.py

async def test_threat_attribution(zerg_state=None):
    """Test GreyNoise threat attribution and scanning pattern analysis"""
    print("Testing GreyNoise threat attribution and scanning pattern analysis")

    assert zerg_state, "this test requires valid zerg_state"

    greynoise_api_key = zerg_state.get("greynoise_api_key").get("value")
    greynoise_base_url = zerg_state.get("greynoise_base_url").get("value")

    from connectors.greynoise.config import GreyNoiseConnectorConfig
    from connectors.greynoise.connector import GreyNoiseConnector
    from connectors.greynoise.target import GreyNoiseTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = GreyNoiseConnectorConfig(
        api_key=greynoise_api_key,
        base_url=greynoise_base_url
    )
    assert isinstance(config, ConnectorConfig), "GreyNoiseConnectorConfig should be of type ConnectorConfig"

    connector = GreyNoiseConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GreyNoiseConnector should be of type Connector"

    greynoise_query_target_options = await connector.get_query_target_options()
    assert isinstance(greynoise_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    query_type_selector = None
    for selector in greynoise_query_target_options.selectors:
        if selector.type == 'query_types':  
            query_type_selector = selector
            break

    assert query_type_selector, "failed to retrieve query type selector from query target options"

    assert isinstance(query_type_selector.values, list), "query_type_selector values must be a list"
    query_type = query_type_selector.values[0] if query_type_selector.values else None
    print(f"Using query type for threat attribution: {query_type}")

    assert query_type, f"failed to retrieve query type from query type selector"

    target = GreyNoiseTarget(query_types=[query_type])
    assert isinstance(target, ConnectorTargetInterface), "GreyNoiseTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_threat_attribution_tool = next(tool for tool in tools if tool.name == "get_threat_attribution")
    
    # Query for scanning patterns and threat attribution
    attribution_result = await get_threat_attribution_tool.execute(
        classification="malicious",
        days_back=7
    )
    threat_attribution = attribution_result.result

    print("Type of returned threat_attribution:", type(threat_attribution))
    print(f"Threat attribution preview: {str(threat_attribution)[:200]}")

    assert threat_attribution is not None, "threat_attribution should not be None"
    
    if isinstance(threat_attribution, dict):
        expected_fields = ["stats", "actors", "scanning_patterns", "classifications", "geographic_data"]
        present_fields = [field for field in expected_fields if field in threat_attribution]
        
        if len(present_fields) > 0:
            print(f"Threat attribution contains these fields: {', '.join(present_fields)}")
            
            if "stats" in threat_attribution:
                stats = threat_attribution["stats"]
                assert isinstance(stats, dict), "Stats should be a dictionary"
                
                stat_fields = ["total_ips", "malicious_count", "benign_count"]
                present_stats = [field for field in stat_fields if field in stats]
                print(f"Stats contain: {', '.join(present_stats)}")
            
            if "actors" in threat_attribution:
                actors = threat_attribution["actors"]
                assert isinstance(actors, list), "Actors should be a list"
                print(f"Found {len(actors)} threat actors")
            
            if "scanning_patterns" in threat_attribution:
                patterns = threat_attribution["scanning_patterns"]
                assert isinstance(patterns, list), "Scanning patterns should be a list"
                print(f"Found {len(patterns)} scanning patterns")
        
        print(f"Threat attribution structure: {threat_attribution}")
        
    elif isinstance(threat_attribution, list):
        assert len(threat_attribution) > 0, "Threat attribution list should not be empty"
        
        sample_item = threat_attribution[0]
        assert isinstance(sample_item, dict), "Attribution items should be dictionaries"
        
        item_fields = ["actor", "classification", "scanning_behavior", "geographic_origin"]
        present_item_fields = [field for field in item_fields if field in sample_item]
        
        print(f"Attribution items contain these fields: {', '.join(present_item_fields)}")
        
        if "classification" in sample_item:
            classification = sample_item["classification"]
            valid_classifications = ["malicious", "benign", "unknown"]
            assert classification in valid_classifications, f"Classification should be valid"
        
        print(f"Example attribution item: {sample_item}")
        
    else:
        assert str(threat_attribution).strip() != "", "Threat attribution should contain meaningful data"

    print(f"Successfully retrieved and validated threat attribution data")

    return True