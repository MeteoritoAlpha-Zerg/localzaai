# 4-test_list_capabilities.py

async def test_list_capabilities(zerg_state=None):
    """Test GreyNoise capability enumeration by way of connector tools"""
    print("Testing GreyNoise capability listing")

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

    num_query_types = 2
    assert isinstance(query_type_selector.values, list), "query_type_selector values must be a list"
    query_types = query_type_selector.values[:num_query_types] if query_type_selector.values else None
    print(f"Selecting query types: {query_types}")

    assert query_types, f"failed to retrieve {num_query_types} query types from query type selector"

    target = GreyNoiseTarget(query_types=query_types)
    assert isinstance(target, ConnectorTargetInterface), "GreyNoiseTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    greynoise_get_capabilities_tool = next(tool for tool in tools if tool.name == "get_greynoise_capabilities")
    greynoise_capabilities_result = await greynoise_get_capabilities_tool.execute()
    greynoise_capabilities = greynoise_capabilities_result.result

    print("Type of returned greynoise_capabilities:", type(greynoise_capabilities))
    print(f"capabilities: {str(greynoise_capabilities)[:200]}")

    assert isinstance(greynoise_capabilities, dict), "greynoise_capabilities should be a dictionary"
    
    expected_fields = ["ip_lookup", "riot", "bulk", "stats", "metadata"]
    present_fields = [field for field in expected_fields if field in greynoise_capabilities]
    
    assert len(present_fields) > 0, f"Capabilities should contain at least one of these fields: {expected_fields}"
    print(f"GreyNoise capabilities contains these fields: {', '.join(present_fields)}")
    
    if "ip_lookup" in greynoise_capabilities:
        ip_lookup = greynoise_capabilities["ip_lookup"]
        assert isinstance(ip_lookup, dict), "IP lookup capability should be a dictionary"
        
        lookup_fields = ["enabled", "rate_limit", "daily_quota"]
        present_lookup_fields = [field for field in lookup_fields if field in ip_lookup]
        print(f"IP lookup contains: {', '.join(present_lookup_fields)}")
    
    if "riot" in greynoise_capabilities:
        riot = greynoise_capabilities["riot"]
        assert isinstance(riot, dict), "RIOT capability should be a dictionary"
    
    print(f"Example capabilities structure: {greynoise_capabilities}")

    print(f"Successfully retrieved and validated GreyNoise capabilities")

    return True