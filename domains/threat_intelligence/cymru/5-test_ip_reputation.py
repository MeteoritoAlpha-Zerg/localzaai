# 5-test_ip_reputation.py

async def test_ip_reputation(zerg_state=None):
    """Test Team Cymru IP reputation and network insights retrieval"""
    print("Attempting to retrieve IP reputation using Team Cymru connector")

    assert zerg_state, "this test requires valid zerg_state"

    teamcymru_api_key = zerg_state.get("teamcymru_api_key").get("value")
    teamcymru_api_secret = zerg_state.get("teamcymru_api_secret").get("value")
    teamcymru_username = zerg_state.get("teamcymru_username").get("value")

    from connectors.teamcymru.config import TeamCymruConnectorConfig
    from connectors.teamcymru.connector import TeamCymruConnector
    from connectors.teamcymru.tools import TeamCymruConnectorTools, GetIPReputationInput
    from connectors.teamcymru.target import TeamCymruTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = TeamCymruConnectorConfig(
        api_key=teamcymru_api_key,
        api_secret=teamcymru_api_secret,
        username=teamcymru_username
    )
    assert isinstance(config, ConnectorConfig), "TeamCymruConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = TeamCymruConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TeamCymruConnector should be of type Connector"

    # get query target options
    teamcymru_query_target_options = await connector.get_query_target_options()
    assert isinstance(teamcymru_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select feed sources to target
    feed_source_selector = None
    for selector in teamcymru_query_target_options.selectors:
        if selector.type == 'feed_source_ids':  
            feed_source_selector = selector
            break

    assert feed_source_selector, "failed to retrieve feed source selector from query target options"

    assert isinstance(feed_source_selector.values, list), "feed_source_selector values must be a list"
    feed_source_id = feed_source_selector.values[0] if feed_source_selector.values else None
    print(f"Selecting feed source ID: {feed_source_id}")

    assert feed_source_id, f"failed to retrieve feed source ID from feed source selector"

    # set up the target with feed source ID
    target = TeamCymruTarget(feed_source_ids=[feed_source_id])
    assert isinstance(target, ConnectorTargetInterface), "TeamCymruTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_ip_reputation tool and execute it with test IPs
    get_ip_reputation_tool = next(tool for tool in tools if tool.name == "get_ip_reputation")
    test_ips = ["8.8.8.8", "1.1.1.1", "192.0.2.1"]
    ip_reputation_result = await get_ip_reputation_tool.execute(ip_addresses=test_ips)
    ip_reputation = ip_reputation_result.result

    print("Type of returned ip_reputation:", type(ip_reputation))
    print(f"IP reputation data: {str(ip_reputation)[:200]}")

    # Verify that ip_reputation is a dictionary or list
    assert isinstance(ip_reputation, (dict, list)), "ip_reputation should be a dictionary or list"
    
    if isinstance(ip_reputation, dict):
        # If it's a dictionary, check each IP
        for ip in test_ips:
            if ip in ip_reputation:
                ip_info = ip_reputation[ip]
                assert "reputation_score" in ip_info, f"IP {ip} should have 'reputation_score' field"
                assert "asn" in ip_info, f"IP {ip} should have 'asn' field"
                assert "country" in ip_info, f"IP {ip} should have 'country' field"
                
                print(f"IP {ip} reputation score: {ip_info.get('reputation_score', 'N/A')}")
    else:
        # If it's a list, verify each entry
        for entry in ip_reputation:
            assert "ip_address" in entry, "Each IP entry should have an 'ip_address' field"
            assert "reputation_score" in entry, "Each IP entry should have a 'reputation_score' field"
    
    # Test ASN lookup if available
    if "get_asn_info" in [tool.name for tool in tools]:
        get_asn_info_tool = next(tool for tool in tools if tool.name == "get_asn_info")
        asn_info_result = await get_asn_info_tool.execute(asn_numbers=["15169", "13335"])
        asn_info = asn_info_result.result
        
        if asn_info:
            assert isinstance(asn_info, (dict, list)), "ASN info should be a dictionary or list"
            print(f"ASN lookup completed")
    
    # Test BGP prefix lookup if available
    if "get_bgp_prefix" in [tool.name for tool in tools]:
        get_bgp_prefix_tool = next(tool for tool in tools if tool.name == "get_bgp_prefix")
        bgp_prefix_result = await get_bgp_prefix_tool.execute(ip_address="8.8.8.8")
        bgp_prefix = bgp_prefix_result.result
        
        if bgp_prefix:
            assert isinstance(bgp_prefix, dict), "BGP prefix should be a dictionary"
            
            bgp_fields = ["prefix", "asn", "as_name", "country"]
            present_bgp_fields = [field for field in bgp_fields if field in bgp_prefix]
            
            print(f"BGP prefix lookup contains: {', '.join(present_bgp_fields)}")

    print(f"Successfully retrieved IP reputation and network insights")

    return True