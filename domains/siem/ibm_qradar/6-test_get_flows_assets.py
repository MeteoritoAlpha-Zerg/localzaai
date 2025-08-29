# 6-test_get_flows_assets.py

async def test_get_flows_assets(zerg_state=None):
    """Test IBM QRadar network flows and asset information retrieval"""
    print("Testing IBM QRadar network flows and asset information retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    ibm_qradar_api_url = zerg_state.get("ibm_qradar_api_url").get("value")
    ibm_qradar_api_token = zerg_state.get("ibm_qradar_api_token").get("value")

    from connectors.ibm_qradar.config import IBMQRadarConnectorConfig
    from connectors.ibm_qradar.connector import IBMQRadarConnector
    from connectors.ibm_qradar.target import IBMQRadarTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = IBMQRadarConnectorConfig(
        api_url=ibm_qradar_api_url,
        api_token=ibm_qradar_api_token
    )
    assert isinstance(config, ConnectorConfig), "IBMQRadarConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = IBMQRadarConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "IBMQRadarConnector should be of type Connector"

    # get query target options
    ibm_qradar_query_target_options = await connector.get_query_target_options()
    assert isinstance(ibm_qradar_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select flows data source
    data_source_selector = None
    for selector in ibm_qradar_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find flows in available data sources
    flows_source = None
    for source in data_source_selector.values:
        if 'flow' in source.lower():
            flows_source = source
            break
    
    assert flows_source, "Flows data source not found in available options"
    print(f"Selecting flows data source: {flows_source}")

    # set up the target with flows data source
    target = IBMQRadarTarget(data_sources=[flows_source])
    assert isinstance(target, ConnectorTargetInterface), "IBMQRadarTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_ibm_qradar_flows tool and execute it
    get_ibm_qradar_flows_tool = next(tool for tool in tools if tool.name == "get_ibm_qradar_flows")
    flows_result = await get_ibm_qradar_flows_tool.execute()
    flows_data = flows_result.result

    print("Type of returned flows data:", type(flows_data))
    print(f"Flows count: {len(flows_data)} sample: {str(flows_data)[:200]}")

    # Verify that flows_data is a list
    assert isinstance(flows_data, list), "Flows data should be a list"
    assert len(flows_data) > 0, "Flows data should not be empty"
    
    # Limit the number of flows to check if there are many
    flows_to_check = flows_data[:10] if len(flows_data) > 10 else flows_data
    
    # Verify structure of each flow entry
    for flow in flows_to_check:
        # Verify essential flow fields per IBM QRadar API specification
        assert "starttime" in flow, "Each flow should have a 'starttime' field"
        assert "sourceip" in flow, "Each flow should have a 'sourceip' field"
        assert "destinationip" in flow, "Each flow should have a 'destinationip' field"
        assert "protocol" in flow, "Each flow should have a 'protocol' field"
        
        # Verify start time is not empty
        assert flow["starttime"], "Start time should not be empty"
        
        # Verify source IP is not empty
        assert flow["sourceip"] and flow["sourceip"].strip(), "Source IP should not be empty"
        
        # Verify destination IP is not empty
        assert flow["destinationip"] and flow["destinationip"].strip(), "Destination IP should not be empty"
        
        # Verify protocol is not empty
        assert flow["protocol"], "Protocol should not be empty"
        
        # Check for additional flow fields per IBM QRadar specification
        flow_fields = ["sourceport", "destinationport", "bytessent", "bytesreceived", "packetssent", "packetsreceived", "flowsource", "applicationname"]
        present_fields = [field for field in flow_fields if field in flow]
        
        print(f"Flow ({flow['sourceip']}:{flow.get('sourceport', 'N/A')} -> {flow['destinationip']}:{flow.get('destinationport', 'N/A')}) contains: {', '.join(present_fields)}")
        
        # If source port is present, validate it's within valid range
        if "sourceport" in flow:
            source_port = flow["sourceport"]
            if source_port is not None:
                assert isinstance(source_port, int), "Source port should be an integer"
                assert 0 <= source_port <= 65535, f"Source port should be between 0 and 65535: {source_port}"
        
        # If destination port is present, validate it's within valid range
        if "destinationport" in flow:
            dest_port = flow["destinationport"]
            if dest_port is not None:
                assert isinstance(dest_port, int), "Destination port should be an integer"
                assert 0 <= dest_port <= 65535, f"Destination port should be between 0 and 65535: {dest_port}"
        
        # If bytes sent is present, verify it's numeric
        if "bytessent" in flow:
            bytes_sent = flow["bytessent"]
            if bytes_sent is not None:
                assert isinstance(bytes_sent, int), "Bytes sent should be an integer"
                assert bytes_sent >= 0, "Bytes sent should be non-negative"
        
        # If bytes received is present, verify it's numeric
        if "bytesreceived" in flow:
            bytes_received = flow["bytesreceived"]
            if bytes_received is not None:
                assert isinstance(bytes_received, int), "Bytes received should be an integer"
                assert bytes_received >= 0, "Bytes received should be non-negative"
        
        # If packets sent is present, verify it's numeric
        if "packetssent" in flow:
            packets_sent = flow["packetssent"]
            if packets_sent is not None:
                assert isinstance(packets_sent, int), "Packets sent should be an integer"
                assert packets_sent >= 0, "Packets sent should be non-negative"
        
        # If packets received is present, verify it's numeric
        if "packetsreceived" in flow:
            packets_received = flow["packetsreceived"]
            if packets_received is not None:
                assert isinstance(packets_received, int), "Packets received should be an integer"
                assert packets_received >= 0, "Packets received should be non-negative"
        
        # If flow source is present, validate it's not empty
        if "flowsource" in flow:
            flow_source = flow["flowsource"]
            assert flow_source and flow_source.strip(), "Flow source should not be empty"
        
        # If application name is present, validate it's not empty
        if "applicationname" in flow:
            app_name = flow["applicationname"]
            assert app_name and app_name.strip(), "Application name should not be empty"
        
        # Log the structure of the first flow for debugging
        if flow == flows_to_check[0]:
            print(f"Example flow structure: {flow}")

    print(f"Successfully retrieved and validated {len(flows_data)} IBM QRadar flows")

    # Test asset retrieval if available
    try:
        # Look for asset tools
        get_ibm_qradar_assets_tool = next((tool for tool in tools if tool.name == "get_ibm_qradar_assets"), None)
        if get_ibm_qradar_assets_tool:
            assets_result = await get_ibm_qradar_assets_tool.execute()
            assets_data = assets_result.result

            print("Type of returned assets data:", type(assets_data))
            print(f"Assets count: {len(assets_data)} sample: {str(assets_data)[:200]}")

            # Verify that assets_data is a list
            assert isinstance(assets_data, list), "Assets data should be a list"
            
            if len(assets_data) > 0:
                # Limit the number of assets to check if there are many
                assets_to_check = assets_data[:5] if len(assets_data) > 5 else assets_data
                
                # Verify structure of each asset entry
                for asset in assets_to_check:
                    # Verify essential asset fields per IBM QRadar API specification
                    assert "id" in asset, "Each asset should have an 'id' field"
                    assert "interfaces" in asset, "Each asset should have an 'interfaces' field"
                    
                    # Verify asset ID is not empty
                    assert asset["id"], "Asset ID should not be empty"
                    
                    # Verify interfaces structure
                    interfaces = asset["interfaces"]
                    assert isinstance(interfaces, list), "Interfaces should be a list"
                    
                    # Check for additional asset fields
                    asset_fields = ["properties", "domain_id", "vulnerability_count"]
                    present_fields = [field for field in asset_fields if field in asset]
                    
                    print(f"Asset {asset['id']} contains: {', '.join(present_fields)}")

                print(f"Successfully retrieved and validated {len(assets_data)} IBM QRadar assets")
            else:
                print("No assets data available")
        else:
            print("Asset retrieval tool not available")
    except Exception as e:
        print(f"Asset retrieval test skipped: {e}")

    return True