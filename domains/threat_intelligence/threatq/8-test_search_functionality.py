# 8-test_search_functionality.py

async def test_search_functionality(zerg_state=None):
    """Test ThreatQ search functionality across multiple object types"""
    print("Attempting to authenticate using ThreatQ connector")

    assert zerg_state, "this test requires valid zerg_state"

    threatq_api_host = zerg_state.get("threatq_api_host").get("value")
    threatq_api_path = zerg_state.get("threatq_api_path").get("value")
    threatq_username = zerg_state.get("threatq_username").get("value")
    threatq_password = zerg_state.get("threatq_password").get("value")
    threatq_client_id = zerg_state.get("threatq_client_id").get("value")

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
        client_id=threatq_client_id
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

    # Find the search tool
    search_tool = next((tool for tool in tools if tool.name == "search"), None)
    assert search_tool is not None, "search tool not found"
    
    # Test 1: First, get some indicator data to use for search terms
    print("\nGetting some data to use for search tests...")
    
    # Find the get_indicators tool
    get_indicators_tool = next((tool for tool in tools if tool.name == "get_indicators"), None)
    assert get_indicators_tool is not None, "get_indicators tool not found"
    
    # Get some indicators to find search terms
    indicators_result = await get_indicators_tool.execute(
        limit=5,
        offset=0
    )
    indicators = indicators_result.result
    
    search_terms = []
    if indicators:
        # Extract some search terms from the indicators
        for indicator in indicators:
            if "value" in indicator and indicator["value"]:
                # Use part of the indicator value as a search term
                # For domain/url, use the domain part
                value = indicator["value"]
                if indicator.get("type") in ["Domain", "URL", "FQDN"]:
                    # Extract domain part without TLD
                    parts = value.split(".")
                    if len(parts) > 1 and len(parts[-2]) > 3:  # Use domain part if it looks reasonable
                        search_terms.append(parts[-2])
                # For IP addresses, use the first octet
                elif indicator.get("type") == "IP":
                    parts = value.split(".")
                    if len(parts) > 0:
                        search_terms.append(parts[0])
                # For other types, use a substring if long enough
                elif len(value) > 5:
                    search_terms.append(value[:5])
    
    # If we couldn't extract any search terms, add some fallback terms
    if not search_terms:
        search_terms = ["malware", "phishing", "attack", "threat"]
    
    # Ensure we have at least one search term
    search_term = search_terms[0] if search_terms else "malware"
    print(f"Using search term: '{search_term}'")
    
    # Test 2: Perform a search across all object types
    print("\nTest 1: Searching across all object types...")
    search_result = await search_tool.execute(
        query=search_term,
        limit=20
    )
    search_results = search_result.result
    
    # Verify the search results structure
    assert isinstance(search_results, dict), "search_results should be a dict"
    
    # Check if we have results
    total_results = 0
    for object_type in search_results:
        if isinstance(search_results[object_type], list):
            total_results += len(search_results[object_type])
    
    if total_results > 0:
        print(f"Found {total_results} total results for search term '{search_term}'")
        
        # Print breakdown by object type
        for object_type in search_results:
            if isinstance(search_results[object_type], list) and search_results[object_type]:
                print(f"  {object_type}: {len(search_results[object_type])} results")
        
        # Show sample results for each object type
        for object_type in search_results:
            if isinstance(search_results[object_type], list) and search_results[object_type]:
                print(f"\nSample {object_type} results:")
                
                # Show up to 3 results per type
                for i, result in enumerate(search_results[object_type][:3]):
                    print(f"  Result {i+1}:")
                    
                    # Print common fields for all object types
                    if "id" in result:
                        print(f"    ID: {result['id']}")
                    
                    # Print type-specific fields
                    if object_type == "indicators":
                        print(f"    Value: {result.get('value', 'N/A')}")
                        print(f"    Type: {result.get('type', 'N/A')}")
                    elif object_type == "events":
                        print(f"    Title: {result.get('title', 'N/A')}")
                        print(f"    Type: {result.get('type', 'N/A')}")
                    elif object_type == "adversaries":
                        print(f"    Name: {result.get('name', 'N/A')}")
                    
                    # Show how the result matched the search
                    if "score" in result:
                        print(f"    Search Score: {result['score']}")
                    
                # Check for essential fields based on object type
                sample_result = search_results[object_type][0]
                if object_type == "indicators":
                    assert "value" in sample_result, "Indicator result missing 'value' field"
                    assert "type" in sample_result, "Indicator result missing 'type' field"
                elif object_type == "adversaries":
                    assert "name" in sample_result, "Adversary result missing 'name' field"
                elif object_type == "events":
                    # Events might have either title or description
                    assert "title" in sample_result or "description" in sample_result, "Event result missing both 'title' and 'description' fields"
    else:
        print(f"No results found for search term '{search_term}'")
    
    # Test 3: Try a more specific search with type filtering
    # Pick another search term if we have multiple
    specific_search_term = search_terms[1] if len(search_terms) > 1 else search_term
    specific_object_type = "indicators"  # Search specifically for indicators
    
    print(f"\nTest 2: Searching specifically for {specific_object_type} with term '{specific_search_term}'...")
    specific_search_result = await search_tool.execute(
        query=specific_search_term,
        limit=10,
        object_type=specific_object_type
    )
    specific_search_results = specific_search_result.result
    
    # Verify the specific search results structure
    assert isinstance(specific_search_results, dict), "specific_search_results should be a dict"
    assert specific_object_type in specific_search_results, f"Results don't contain the requested object type: {specific_object_type}"
    
    # Check if we have specific results
    if specific_object_type in specific_search_results and isinstance(specific_search_results[specific_object_type], list) and specific_search_results[specific_object_type]:
        type_results = specific_search_results[specific_object_type]
        print(f"Found {len(type_results)} {specific_object_type} for search term '{specific_search_term}'")
        
        # Show sample results
        for i, result in enumerate(type_results[:5]):  # Show up to 5 results
            print(f"  Result {i+1}:")
            
            # Print type-specific fields
            if specific_object_type == "indicators":
                print(f"    Value: {result.get('value', 'N/A')}")
                print(f"    Type: {result.get('type', 'N/A')}")
                print(f"    Status: {result.get('status', 'N/A')}")
            
            # Show how the result matched the search
            if "score" in result:
                print(f"    Search Score: {result['score']}")
    else:
        print(f"No {specific_object_type} found for search term '{specific_search_term}'")
    
    # Test 4: Perform a search with additional parameters
    print("\nTest 3: Performing an advanced search with additional parameters...")
    
    # Try to get a more common search term if we have multiple
    advanced_search_term = search_terms[2] if len(search_terms) > 2 else search_term
    
    advanced_search_result = await search_tool.execute(
        query=advanced_search_term,
        limit=15,  # Increased limit
        min_score=0.3,  # Minimum relevance score
        with_attributes=True,  # Include attributes in results
        with_sources=True  # Include sources in results
    )
    advanced_search_results = advanced_search_result.result
    
    # Verify the advanced search results structure
    assert isinstance(advanced_search_results, dict), "advanced_search_results should be a dict"
    
    # Check if we have results
    advanced_total_results = 0
    for object_type in advanced_search_results:
        if isinstance(advanced_search_results[object_type], list):
            advanced_total_results += len(advanced_search_results[object_type])
    
    if advanced_total_results > 0:
        print(f"Found {advanced_total_results} total results for advanced search with term '{advanced_search_term}'")
        
        # Print breakdown by object type
        for object_type in advanced_search_results:
            if isinstance(advanced_search_results[object_type], list) and advanced_search_results[object_type]:
                print(f"  {object_type}: {len(advanced_search_results[object_type])} results")
        
        # Check for enriched data (attributes and sources)
        for object_type in advanced_search_results:
            if isinstance(advanced_search_results[object_type], list) and advanced_search_results[object_type]:
                sample_result = advanced_search_results[object_type][0]
                
                # Check for attributes
                if "attributes" in sample_result and sample_result["attributes"]:
                    print(f"\nFound attributes in {object_type} results:")
                    for attr in sample_result["attributes"][:3]:  # Show up to 3 attributes
                        print(f"  {attr.get('name', 'Unknown')}: {attr.get('value', 'N/A')}")
                
                # Check for sources
                if "sources" in sample_result and sample_result["sources"]:
                    print(f"\nFound sources in {object_type} results:")
                    for source in sample_result["sources"][:3]:  # Show up to 3 sources
                        print(f"  {source.get('name', 'Unknown')}")
                
                # Break after checking one type
                break
    else:
        print(f"No results found for advanced search with term '{advanced_search_term}'")

    print("\nSuccessfully completed search functionality test")
    return True