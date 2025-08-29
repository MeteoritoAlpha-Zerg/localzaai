# 4-test_get_flows.py

async def test_get_flows(zerg_state=None):
    """Test Cisco Stealthwatch network flow data retrieval"""
    print("Testing Cisco Stealthwatch network flow data retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    cisco_stealthwatch_api_url = zerg_state.get("cisco_stealthwatch_api_url").get("value")
    cisco_stealthwatch_username = zerg_state.get("cisco_stealthwatch_username").get("value")
    cisco_stealthwatch_password = zerg_state.get("cisco_stealthwatch_password").get("value")

    from connectors.cisco_stealthwatch.config import CiscoStealthwatchConnectorConfig
    from connectors.cisco_stealthwatch.connector import CiscoStealthwatchConnector
    from connectors.cisco_stealthwatch.target import CiscoStealthwatchTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = CiscoStealthwatchConnectorConfig(
        api_url=cisco_stealthwatch_api_url,
        username=cisco_stealthwatch_username,
        password=cisco_stealthwatch_password
    )
    assert isinstance(config, ConnectorConfig), "CiscoStealthwatchConnectorConfig should be of type ConnectorConfig"

    connector = CiscoStealthwatchConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CiscoStealthwatchConnector should be of type Connector"

    cisco_stealthwatch_query_target_options = await connector.get_query_target_options()
    assert isinstance(cisco_stealthwatch_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    data_source_selector = None
    for selector in cisco_stealthwatch_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    flows_source = None
    for source in data_source_selector.values:
        if 'flow' in source.lower():
            flows_source = source
            break
    
    assert flows_source, "Flows data source not found in available options"
    print(f"Selecting flows data source: {flows_source}")

    target = CiscoStealthwatchTarget(data_sources=[flows_source])
    assert isinstance(target, ConnectorTargetInterface), "CiscoStealthwatchTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    cisco_stealthwatch_get_flows_tool = next(tool for tool in tools if tool.name == "get_cisco_stealthwatch_flows")
    flows_result = await cisco_stealthwatch_get_flows_tool.execute()
    flows_data = flows_result.result

    print("Type of returned flows data:", type(flows_data))
    print(f"Flows count: {len(flows_data)} sample: {str(flows_data)[:200]}")

    assert isinstance(flows_data, list), "Flows data should be a list"
    assert len(flows_data) > 0, "Flows data should not be empty"
    
    flows_to_check = flows_data[:10] if len(flows_data) > 10 else flows_data
    
    for flow in flows_to_check:
        # Verify essential flow fields per Cisco Stealthwatch API specification
        assert "peer_ip" in flow, "Each flow should have a 'peer_ip' field"
        assert "subject_ip" in flow, "Each flow should have a 'subject_ip' field"
        assert "protocol" in flow, "Each flow should have a 'protocol' field"
        assert "start_time" in flow, "Each flow should have a 'start_time' field"
        
        assert flow["peer_ip"] and flow["peer_ip"].strip(), "Peer IP should not be empty"
        assert flow["subject_ip"] and flow["subject_ip"].strip(), "Subject IP should not be empty"
        assert flow["protocol"], "Protocol should not be empty"
        assert flow["start_time"], "Start time should not be empty"
        
        flow_fields = ["port", "bytes_sent", "bytes_received", "packets_sent", "packets_received", "duration", "service"]
        present_fields = [field for field in flow_fields if field in flow]
        
        print(f"Flow ({flow['subject_ip']} -> {flow['peer_ip']}, {flow['protocol']}) contains: {', '.join(present_fields)}")
        
        # If port is present, validate it's within valid range
        if "port" in flow:
            port = flow["port"]
            if port is not None:
                assert isinstance(port, int), "Port should be an integer"
                assert 0 <= port <= 65535, f"Port should be between 0 and 65535: {port}"
        
        # If bytes sent is present, verify it's numeric
        if "bytes_sent" in flow:
            bytes_sent = flow["bytes_sent"]
            if bytes_sent is not None:
                assert isinstance(bytes_sent, int), "Bytes sent should be an integer"
                assert bytes_sent >= 0, "Bytes sent should be non-negative"
        
        # If bytes received is present, verify it's numeric
        if "bytes_received" in flow:
            bytes_received = flow["bytes_received"]
            if bytes_received is not None:
                assert isinstance(bytes_received, int), "Bytes received should be an integer"
                assert bytes_received >= 0, "Bytes received should be non-negative"
        
        # If packets sent is present, verify it's numeric
        if "packets_sent" in flow:
            packets_sent = flow["packets_sent"]
            if packets_sent is not None:
                assert isinstance(packets_sent, int), "Packets sent should be an integer"
                assert packets_sent >= 0, "Packets sent should be non-negative"
        
        # If packets received is present, verify it's numeric
        if "packets_received" in flow:
            packets_received = flow["packets_received"]
            if packets_received is not None:
                assert isinstance(packets_received, int), "Packets received should be an integer"
                assert packets_received >= 0, "Packets received should be non-negative"
        
        # Log the structure of the first flow for debugging
        if flow == flows_to_check[0]:
            print(f"Example flow structure: {flow}")

    print(f"Successfully retrieved and validated {len(flows_data)} Cisco Stealthwatch flows")

    return True