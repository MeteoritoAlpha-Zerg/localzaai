# 7-test_network_topology.py

async def test_network_topology(zerg_state=None):
    """Test Claroty network topology and communication analysis retrieval by way of connector tools"""
    print("Attempting to authenticate using Claroty connector")

    assert zerg_state, "this test requires valid zerg_state"

    claroty_server_url = zerg_state.get("claroty_server_url").get("value")
    claroty_api_token = zerg_state.get("claroty_api_token").get("value")
    claroty_username = zerg_state.get("claroty_username").get("value")
    claroty_password = zerg_state.get("claroty_password").get("value")
    claroty_api_version = zerg_state.get("claroty_api_version").get("value")

    from connectors.claroty.config import ClarotyConnectorConfig
    from connectors.claroty.connector import ClarotyConnector
    from connectors.claroty.tools import ClarotyConnectorTools, GetNetworkTopologyInput
    from connectors.claroty.target import ClarotyTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ClarotyConnectorConfig(
        server_url=claroty_server_url,
        api_token=claroty_api_token,
        username=claroty_username,
        password=claroty_password,
        api_version=claroty_api_version
    )
    assert isinstance(config, ConnectorConfig), "ClarotyConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ClarotyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ClarotyConnector should be of type Connector"

    # get query target options
    claroty_query_target_options = await connector.get_query_target_options()
    assert isinstance(claroty_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select security zones to target
    zone_selector = None
    for selector in claroty_query_target_options.selectors:
        if selector.type == 'security_zones':  
            zone_selector = selector
            break

    security_zone = None
    if zone_selector and isinstance(zone_selector.values, list) and zone_selector.values:
        security_zone = zone_selector.values[0]
        print(f"Selecting security zone: {security_zone}")

    # select asset types to target (optional for network topology)
    asset_type_selector = None
    for selector in claroty_query_target_options.selectors:
        if selector.type == 'asset_types':  
            asset_type_selector = selector
            break

    asset_type = None
    if asset_type_selector and isinstance(asset_type_selector.values, list) and asset_type_selector.values:
        asset_type = asset_type_selector.values[0]
        print(f"Selecting asset type: {asset_type}")

    # set up the target with security zones and asset types
    target = ClarotyTarget(security_zones=[security_zone] if security_zone else None, asset_types=[asset_type] if asset_type else None)
    assert isinstance(target, ConnectorTargetInterface), "ClarotyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_claroty_network_topology tool and execute it
    get_network_topology_tool = next(tool for tool in tools if tool.name == "get_claroty_network_topology")
    
    # Get network topology with communication flows and protocol analysis
    topology_result = await get_network_topology_tool.execute(include_communication_flows=True, include_protocol_analysis=True, time_range="24h")
    claroty_network_topology = topology_result.result

    print("Type of returned claroty_network_topology:", type(claroty_network_topology))
    print(f"network topology data: {str(claroty_network_topology)[:200]}")

    # Verify that claroty_network_topology is a dictionary
    assert isinstance(claroty_network_topology, dict), "claroty_network_topology should be a dictionary"
    assert len(claroty_network_topology) > 0, "claroty_network_topology should not be empty"
    
    # Verify essential network topology structure
    assert "nodes" in claroty_network_topology, "Network topology should have a 'nodes' field"
    assert "connections" in claroty_network_topology, "Network topology should have a 'connections' field"
    
    nodes = claroty_network_topology["nodes"]
    connections = claroty_network_topology["connections"]
    
    assert isinstance(nodes, list), "Network nodes should be a list"
    assert isinstance(connections, list), "Network connections should be a list"
    assert len(nodes) > 0, "Network topology should contain nodes"
    
    print(f"Network topology contains {len(nodes)} nodes and {len(connections)} connections")
    
    # Limit the number of nodes to check if there are many
    nodes_to_check = nodes[:5] if len(nodes) > 5 else nodes
    
    # Verify structure of each network node
    for node in nodes_to_check:
        # Verify essential network node fields
        assert "id" in node, "Each node should have an 'id' field"
        assert "ip_address" in node, "Each node should have an 'ip_address' field"
        assert "node_type" in node, "Each node should have a 'node_type' field"
        
        # Verify IP address format (basic validation)
        ip_address = node["ip_address"]
        assert isinstance(ip_address, str), "IP address should be a string"
        assert len(ip_address.split(".")) == 4 or ":" in ip_address, "IP should be IPv4 or IPv6 format"
        
        # Check for network node categorization
        node_type = node["node_type"]
        valid_node_types = ["asset", "network_device", "server", "workstation", "unknown"]
        assert node_type in valid_node_types, f"Node type {node_type} should be one of {valid_node_types}"
        
        # Check for asset information if node represents an OT/ICS asset
        if node_type == "asset":
            asset_fields = ["asset_name", "asset_type", "vendor", "model", "firmware_version"]
            present_asset = [field for field in asset_fields if field in node]
            print(f"Asset node {node['id']} contains: {', '.join(present_asset)}")
            
            # Verify asset type matches target if specified
            if asset_type and "asset_type" in node:
                assert node["asset_type"] == asset_type, f"Asset type {node['asset_type']} should match target {asset_type}"
        
        # Check for network device information
        network_fields = ["mac_address", "subnet", "vlan", "network_segment", "security_zone"]
        present_network = [field for field in network_fields if field in node]
        print(f"Node {node['id']} contains these network fields: {', '.join(present_network)}")
        
        # Verify security zone context if zones were selected
        if security_zone and "security_zone" in node:
            assert node["security_zone"] == security_zone, f"Security zone {node['security_zone']} should match target {security_zone}"
        
        # Check for operational status and monitoring
        status_fields = ["status", "last_seen", "availability", "response_time"]
        present_status = [field for field in status_fields if field in node]
        print(f"Node {node['id']} contains these status fields: {', '.join(present_status)}")
        
        # Check for protocol and service information
        protocol_fields = ["protocols", "services", "open_ports", "communication_protocols"]
        present_protocol = [field for field in protocol_fields if field in node]
        print(f"Node {node['id']} contains these protocol fields: {', '.join(present_protocol)}")
    
    # Verify structure of network connections if any exist
    if len(connections) > 0:
        connections_to_check = connections[:5] if len(connections) > 5 else connections
        
        for connection in connections_to_check:
            # Verify essential connection fields
            assert "source_node" in connection, "Each connection should have a 'source_node' field"
            assert "destination_node" in connection, "Each connection should have a 'destination_node' field"
            assert "protocol" in connection, "Each connection should have a 'protocol' field"
            
            # Check for communication flow details
            flow_fields = ["port", "direction", "frequency", "data_volume", "last_communication"]
            present_flow = [field for field in flow_fields if field in connection]
            print(f"Connection contains these flow fields: {', '.join(present_flow)}")
            
            # Check for protocol analysis details
            analysis_fields = ["protocol_analysis", "anomalies", "risk_indicators", "baseline_deviation"]
            present_analysis = [field for field in analysis_fields if field in connection]
            print(f"Connection contains these analysis fields: {', '.join(present_analysis)}")
            
            # Verify nodes referenced in connection exist in nodes list
            source_node = connection["source_node"]
            dest_node = connection["destination_node"]
            node_ids = [node["id"] for node in nodes]
            assert source_node in node_ids, f"Source node {source_node} should exist in nodes list"
            assert dest_node in node_ids, f"Destination node {dest_node} should exist in nodes list"
    
    # Check for network topology metadata
    topology_metadata_fields = ["discovery_time", "coverage_percentage", "network_segments", "security_zones_mapped"]
    present_metadata = [field for field in topology_metadata_fields if field in claroty_network_topology]
    print(f"Network topology contains these metadata fields: {', '.join(present_metadata)}")
    
    # Check for network segmentation analysis
    if "network_segments" in claroty_network_topology:
        segments = claroty_network_topology["network_segments"]
        assert isinstance(segments, list), "Network segments should be a list"
        
        for segment in segments[:3]:  # Check first 3 segments
            segment_fields = ["segment_id", "subnet", "description", "security_level", "asset_count"]
            present_segment = [field for field in segment_fields if field in segment]
            print(f"Network segment contains: {', '.join(present_segment)}")
    
    # Check for protocol analysis summary
    if "protocol_analysis" in claroty_network_topology:
        protocol_analysis = claroty_network_topology["protocol_analysis"]
        assert isinstance(protocol_analysis, dict), "Protocol analysis should be a dictionary"
        
        analysis_summary_fields = ["detected_protocols", "anomalous_communications", "security_findings", "baseline_metrics"]
        present_analysis_summary = [field for field in analysis_summary_fields if field in protocol_analysis]
        print(f"Protocol analysis contains: {', '.join(present_analysis_summary)}")
    
    # Log the overall structure for debugging
    print(f"Network topology structure keys: {list(claroty_network_topology.keys())}")

    print(f"Successfully retrieved and validated Claroty network topology with {len(nodes)} nodes and {len(connections)} connections")

    return True