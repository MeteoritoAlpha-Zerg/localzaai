# 5-test_ip_intelligence.py

async def test_ip_intelligence(zerg_state=None):
    """Test GreyNoise IP intelligence retrieval"""
    print("Testing GreyNoise IP intelligence retrieval")

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
    print(f"Selecting query type: {query_type}")

    assert query_type, f"failed to retrieve query type from query type selector"

    target = GreyNoiseTarget(query_types=[query_type])
    assert isinstance(target, ConnectorTargetInterface), "GreyNoiseTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    lookup_ip_tool = next(tool for tool in tools if tool.name == "lookup_ip")
    
    # Test with a known public IP (Google DNS)
    test_ip = "8.8.8.8"
    
    ip_lookup_result = await lookup_ip_tool.execute(ip_address=test_ip)
    ip_intelligence = ip_lookup_result.result

    print("Type of returned ip_intelligence:", type(ip_intelligence))
    print(f"IP intelligence preview: {str(ip_intelligence)[:200]}")

    assert ip_intelligence is not None, "ip_intelligence should not be None"
    
    if isinstance(ip_intelligence, dict):
        expected_fields = ["ip", "seen", "classification", "first_seen", "last_seen", "actor", "tags"]
        present_fields = [field for field in expected_fields if field in ip_intelligence]
        
        if len(present_fields) > 0:
            print(f"IP intelligence contains these fields: {', '.join(present_fields)}")
            
            if "ip" in ip_intelligence:
                ip_addr = ip_intelligence["ip"]
                assert ip_addr == test_ip, f"Returned IP should match queried IP"
            
            if "classification" in ip_intelligence:
                classification = ip_intelligence["classification"]
                valid_classifications = ["malicious", "benign", "unknown"]
                assert classification in valid_classifications, f"Classification should be valid"
            
            if "seen" in ip_intelligence:
                seen = ip_intelligence["seen"]
                assert isinstance(seen, bool), "Seen field should be boolean"
            
            if "tags" in ip_intelligence:
                tags = ip_intelligence["tags"]
                assert isinstance(tags, list), "Tags should be a list"
        
        print(f"IP intelligence structure: {ip_intelligence}")
        
    else:
        assert str(ip_intelligence).strip() != "", "IP intelligence should contain meaningful data"

    print(f"Successfully retrieved IP intelligence for {test_ip}")

    return True