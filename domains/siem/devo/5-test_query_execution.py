# 5-test_query_execution.py

async def test_query_execution(zerg_state=None):
    """Test Devo query execution and security data retrieval"""
    print("Attempting to execute queries using Devo connector")

    assert zerg_state, "this test requires valid zerg_state"

    devo_url = zerg_state.get("devo_url").get("value")
    devo_api_key = zerg_state.get("devo_api_key", {}).get("value")
    devo_api_secret = zerg_state.get("devo_api_secret", {}).get("value")
    devo_oauth_token = zerg_state.get("devo_oauth_token", {}).get("value")
    devo_domain = zerg_state.get("devo_domain").get("value")

    from connectors.devo.config import DevoConnectorConfig
    from connectors.devo.connector import DevoConnector
    from connectors.devo.tools import DevoConnectorTools
    from connectors.devo.target import DevoTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config - prefer OAuth token over API key/secret
    if devo_oauth_token:
        config = DevoConnectorConfig(
            url=devo_url,
            oauth_token=devo_oauth_token,
            default_domain=devo_domain,
        )
    elif devo_api_key and devo_api_secret:
        config = DevoConnectorConfig(
            url=devo_url,
            api_key=devo_api_key,
            api_secret=devo_api_secret,
            default_domain=devo_domain,
        )
    else:
        raise Exception("Either devo_oauth_token or both devo_api_key and devo_api_secret must be provided")

    assert isinstance(config, ConnectorConfig), "DevoConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = DevoConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DevoConnector should be of type Connector"

    # get query target options
    devo_query_target_options = await connector.get_query_target_options()
    assert isinstance(devo_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select domains to target
    domain_selector = None
    for selector in devo_query_target_options.selectors:
        if selector.type == 'domain_names':  
            domain_selector = selector
            break

    assert domain_selector, "failed to retrieve domain selector from query target options"

    assert isinstance(domain_selector.values, list), "domain_selector values must be a list"
    domain_name = domain_selector.values[0] if domain_selector.values else None
    print(f"Selecting domain name: {domain_name}")

    assert domain_name, f"failed to retrieve domain name from domain selector"

    # set up the target with domain names
    target = DevoTarget(domain_names=[domain_name])
    assert isinstance(target, ConnectorTargetInterface), "DevoTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the execute_devo_query tool and execute it with a basic LINQ query
    execute_devo_query_tool = next(tool for tool in tools if tool.name == "execute_devo_query")
    
    # Use a basic Devo LINQ query that should work on most security data
    test_query = f"from {domain_name} select * limit 100"
    
    devo_query_result = await execute_devo_query_tool.execute(
        query=test_query,
        from_date="2024-01-01T00:00:00Z",
        to_date="2024-12-31T23:59:59Z",
        timeout=300  # 5 minute timeout for testing
    )
    devo_query_data = devo_query_result.result

    print("Type of returned devo_query_data:", type(devo_query_data))
    print(f"len query results: {len(devo_query_data)} results: {str(devo_query_data)[:200]}")

    # Verify that devo_query_data is a list
    assert isinstance(devo_query_data, list), "devo_query_data should be a list"
    assert len(devo_query_data) > 0, "devo_query_data should not be empty"
    
    # Limit the number of results to check if there are many
    results_to_check = devo_query_data[:5] if len(devo_query_data) > 5 else devo_query_data
    
    # Verify structure of each query result object
    for result in results_to_check:
        # Verify essential Devo query result fields
        assert isinstance(result, dict), "Each result should be a dictionary"
        
        # Check for common SIEM data fields (these may vary by domain)
        common_fields = ["eventdate", "timestamp", "srcip", "dstip", "srcport", "dstport", "protocol", "event", "severity"]
        present_common = [field for field in common_fields if field in result]
        
        print(f"Query result contains these common SIEM fields: {', '.join(present_common)}")
        
        # Log the structure of the first result for debugging
        if result == results_to_check[0]:
            print(f"Example query result structure: {result}")

    print(f"Successfully executed Devo query and validated {len(devo_query_data)} results")

    # Test aggregation query as well
    aggregation_query = f"from {domain_name} group by srcip select srcip, count() as event_count limit 10"
    
    devo_aggregation_result = await execute_devo_query_tool.execute(
        query=aggregation_query,
        from_date="2024-01-01T00:00:00Z",
        to_date="2024-12-31T23:59:59Z",
        timeout=300
    )
    devo_aggregation_data = devo_aggregation_result.result

    print("Type of returned devo_aggregation_data:", type(devo_aggregation_data))
    
    # Verify aggregation structure
    assert isinstance(devo_aggregation_data, list), "devo_aggregation_data should be a list"
    
    if len(devo_aggregation_data) > 0:
        # Check aggregation results
        aggregation_to_check = devo_aggregation_data[:3] if len(devo_aggregation_data) > 3 else devo_aggregation_data
        
        for aggregation in aggregation_to_check:
            assert "srcip" in aggregation, "Each aggregation result should have a 'srcip' field"
            assert "event_count" in aggregation, "Each aggregation result should have an 'event_count' field"
            
            print(f"Aggregation result: {aggregation['srcip']} has {aggregation['event_count']} events")
        
        print(f"Successfully retrieved and validated {len(devo_aggregation_data)} Devo aggregation results")

    # Test security-focused query
    security_query = f"from {domain_name} where severity >= 'medium' select eventdate, srcip, dstip, event, severity limit 50"
    
    devo_security_result = await execute_devo_query_tool.execute(
        query=security_query,
        from_date="2024-01-01T00:00:00Z",
        to_date="2024-12-31T23:59:59Z",
        timeout=300
    )
    devo_security_data = devo_security_result.result

    print("Type of returned devo_security_data:", type(devo_security_data))
    
    # Verify security query structure
    assert isinstance(devo_security_data, list), "devo_security_data should be a list"
    
    # Security data might be empty, which is acceptable
    if len(devo_security_data) > 0:
        # Check security results
        security_to_check = devo_security_data[:3] if len(devo_security_data) > 3 else devo_security_data
        
        for security in security_to_check:
            # Verify security-specific fields
            security_fields = ["eventdate", "severity", "event"]
            present_security_fields = [field for field in security_fields if field in security]
            
            print(f"Security result contains these fields: {', '.join(present_security_fields)}")

        print(f"Successfully retrieved and validated {len(devo_security_data)} Devo security results")
    else:
        print("No security data found with medium+ severity - this is acceptable for testing")

    return True