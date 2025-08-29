# 5-test_indicator_retrieval.py

async def test_indicator_retrieval(zerg_state=None):
    """Test ThreatQ indicator retrieval with filtering capabilities"""
    print("Attempting to authenticate using ThreatQ connector")

    assert zerg_state, "this test requires valid zerg_state"

    threatq_api_host = zerg_state.get("threatq_api_host").get("value")
    threatq_api_path = zerg_state.get("threatq_api_path").get("value")
    threatq_username = zerg_state.get("threatq_username").get("value")
    threatq_password = zerg_state.get("threatq_password").get("value")
    threatq_client_id = zerg_state.get("threatq_client_id").get("value")
    min_score = zerg_state.get("threatq_indicator_min_score", {"value": 1}).get("value")
    max_score = zerg_state.get("threatq_indicator_max_score", {"value": 100}).get("value")
    page_size = zerg_state.get("threatq_indicator_page_size", {"value": 100}).get("value")

    from connectors.threatq.config import ThreatQConnectorConfig
    from connectors.threatq.connector import ThreatQConnector
    from connectors.threatq.target import ThreatQTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ThreatQConnectorConfig(
        api_host=threatq_api_host,
        api_path=threatq_api_path,
        username=threatq_username,
        password=threatq_password,
        client_id=threatq_client_id,
        indicator_min_score=min_score,
        indicator_max_score=max_score,
        indicator_page_size=page_size
    )
    assert isinstance(config, ConnectorConfig), "ThreatQConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ThreatQConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ThreatQConnector should be of type Connector"

    # get query target options
    threatq_query_target_options = await connector.get_query_target_options()
    assert isinstance(threatq_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # set up the target
    target = ThreatQTarget()
    assert isinstance(target, ConnectorTargetInterface), "ThreatQTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Find the get_indicators tool
    get_indicators_tool = next((tool for tool in tools if tool.name == "get_indicators"), None)
    assert get_indicators_tool is not None, "get_indicators tool not found"
    
    # Test 1: Get all indicators with default settings
    print("\nTest 1: Retrieving all indicators with default settings...")
    indicators_result = await get_indicators_tool.execute(
        limit=25,  # Limit to 25 for testing
        offset=0
    )
    indicators = indicators_result.result

    print(f"Retrieved {len(indicators)} indicators")
    assert isinstance(indicators, list), "indicators should be a list"
    
    if indicators:
        print("\nSample indicator from default query:")
        sample_indicator = indicators[0]
        
        # Print basic info
        print(f"ID: {sample_indicator.get('id')}")
        print(f"Value: {sample_indicator.get('value')}")
        print(f"Type: {sample_indicator.get('type')}")
        
        # Check essential fields
        essential_fields = ["id", "value", "type"]
        for field in essential_fields:
            assert field in sample_indicator, f"Indicator missing essential field: {field}"
    else:
        print("No indicators found with default settings")
    
    # Test 2: Get indicators with type filter
    print("\nTest 2: Retrieving indicators with type filter...")
    indicator_types = ["URL", "IP", "Hash", "Domain", "Email", "FQDN"]
    
    # Try to find a type that has indicators
    found_type_with_indicators = False
    for indicator_type in indicator_types:
        indicators_by_type_result = await get_indicators_tool.execute(
            limit=10,
            offset=0,
            type=indicator_type
        )
        indicators_by_type = indicators_by_type_result.result
        
        if indicators_by_type:
            found_type_with_indicators = True
            print(f"Found {len(indicators_by_type)} indicators of type '{indicator_type}'")
            
            # Verify that all indicators are of the requested type
            for indicator in indicators_by_type:
                assert indicator["type"] == indicator_type, f"Indicator type {indicator['type']} doesn't match requested type {indicator_type}"
            
            # Check one sample indicator of this type
            sample_indicator = indicators_by_type[0]
            print(f"\nSample {indicator_type} indicator:")
            print(f"ID: {sample_indicator.get('id')}")
            print(f"Value: {sample_indicator.get('value')}")
            print(f"Status: {sample_indicator.get('status', 'N/A')}")
            print(f"Score: {sample_indicator.get('score', 'N/A')}")
            
            # Break after finding a type with indicators
            break
    
    if not found_type_with_indicators:
        print("No indicators found for any of the standard types")
        
    # Test 3: Get indicators with detailed information
    print("\nTest 3: Retrieving indicators with attributes, sources, and related data...")
    detailed_indicators_result = await get_indicators_tool.execute(
        limit=5,
        offset=0,
        with_attributes=True,
        with_sources=True,
        with_adversaries=True
    )
    detailed_indicators = detailed_indicators_result.result
    
    if detailed_indicators:
        print(f"Retrieved {len(detailed_indicators)} indicators with detailed information")
        
        # Check a sample detailed indicator
        detailed_sample = detailed_indicators[0]
        print(f"\nDetailed indicator information:")
        print(f"ID: {detailed_sample.get('id')}")
        print(f"Value: {detailed_sample.get('value')}")
        print(f"Type: {detailed_sample.get('type')}")
        
        # Check for attributes
        if "attributes" in detailed_sample and detailed_sample["attributes"]:
            print("\nAttributes:")
            assert isinstance(detailed_sample["attributes"], list), "attributes should be a list"
            for attr in detailed_sample["attributes"][:5]:  # Show up to 5 attributes
                assert "name" in attr, "Attribute missing 'name' field"
                assert "value" in attr, "Attribute missing 'value' field"
                print(f"  {attr['name']}: {attr['value']}")
        
        # Check for sources
        if "sources" in detailed_sample and detailed_sample["sources"]:
            print("\nSources:")
            assert isinstance(detailed_sample["sources"], list), "sources should be a list"
            for source in detailed_sample["sources"][:5]:  # Show up to 5 sources
                assert "name" in source, "Source missing 'name' field"
                print(f"  {source['name']}")
        
        # Check for adversaries
        if "adversaries" in detailed_sample and detailed_sample["adversaries"]:
            print("\nRelated Adversaries:")
            assert isinstance(detailed_sample["adversaries"], list), "adversaries should be a list"
            for adversary in detailed_sample["adversaries"][:5]:  # Show up to 5 adversaries
                assert "name" in adversary, "Adversary missing 'name' field"
                print(f"  {adversary['name']}")
    else:
        print("No indicators found with detailed information")
    
    # Test 4: Get indicators with score filter
    print("\nTest 4: Retrieving indicators with score filter...")
    high_score_indicators_result = await get_indicators_tool.execute(
        limit=10,
        offset=0,
        min_score=75,  # Filter for high-scoring indicators
        with_attributes=True
    )
    high_score_indicators = high_score_indicators_result.result
    
    if high_score_indicators:
        print(f"Found {len(high_score_indicators)} high-scoring indicators (score >= 75)")
        
        # Verify scores are in the requested range
        for indicator in high_score_indicators:
            if "score" in indicator:
                assert indicator["score"] >= 75, f"Indicator score {indicator['score']} is below the requested minimum of 75"
        
        # Check one sample high-scoring indicator
        high_score_sample = high_score_indicators[0]
        print(f"\nSample high-scoring indicator:")
        print(f"ID: {high_score_sample.get('id')}")
        print(f"Value: {high_score_sample.get('value')}")
        print(f"Type: {high_score_sample.get('type')}")
        print(f"Score: {high_score_sample.get('score', 'N/A')}")
    else:
        print("No high-scoring indicators found")
    
    # Test 5: Get a specific indicator by ID
    if indicators:
        indicator_id = indicators[0]["id"]
        print(f"\nTest 5: Retrieving specific indicator by ID: {indicator_id}")
        
        # Find the get_indicator_by_id tool
        get_indicator_by_id_tool = next((tool for tool in tools if tool.name == "get_indicator_by_id"), None)
        
        if get_indicator_by_id_tool:
            indicator_detail_result = await get_indicator_by_id_tool.execute(
                indicator_id=indicator_id,
                with_attributes=True,
                with_sources=True,
                with_adversaries=True
            )
            indicator_detail = indicator_detail_result.result
            
            # Verify the detailed indicator data structure
            assert isinstance(indicator_detail, dict), "indicator_detail should be a dict"
            assert indicator_detail["id"] == indicator_id, "Returned indicator ID doesn't match requested ID"
            
            print("\nDetailed Indicator Information:")
            print(f"ID: {indicator_detail['id']}")
            print(f"Value: {indicator_detail['value']}")
            print(f"Type: {indicator_detail['type']}")
            
            # Print any additional fields in the detailed view
            additional_fields = ["status", "score", "created_at", "updated_at", "description"]
            for field in additional_fields:
                if field in indicator_detail:
                    print(f"{field.replace('_', ' ').title()}: {indicator_detail[field]}")
        else:
            print("get_indicator_by_id tool not found, skipping detailed indicator retrieval test")
    else:
        print("No indicators available to test specific ID retrieval")

    print("\nSuccessfully completed indicator retrieval tests")
    return True