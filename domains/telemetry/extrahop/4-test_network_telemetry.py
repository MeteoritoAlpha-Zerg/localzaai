# 4-test_network_telemetry.py

async def test_network_telemetry(zerg_state=None):
    """Test ExtraHop network telemetry enumeration by way of connector tools"""
    print("Attempting to retrieve ExtraHop network telemetry using ExtraHop connector")

    assert zerg_state, "this test requires valid zerg_state"

    extrahop_server_url = zerg_state.get("extrahop_server_url").get("value")
    extrahop_api_key = zerg_state.get("extrahop_api_key").get("value")
    extrahop_api_secret = zerg_state.get("extrahop_api_secret").get("value")

    from connectors.extrahop.config import ExtraHopConnectorConfig
    from connectors.extrahop.connector import ExtraHopConnector
    from connectors.extrahop.tools import ExtraHopConnectorTools
    from connectors.extrahop.target import ExtraHopTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = ExtraHopConnectorConfig(
        server_url=extrahop_server_url,
        api_key=extrahop_api_key,
        api_secret=extrahop_api_secret
    )
    assert isinstance(config, ConnectorConfig), "ExtraHopConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ExtraHopConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ExtraHopConnector should be of type Connector"

    # get query target options
    extrahop_query_target_options = await connector.get_query_target_options()
    assert isinstance(extrahop_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select sensor networks to target
    sensor_network_selector = None
    for selector in extrahop_query_target_options.selectors:
        if selector.type == 'sensor_network_ids':  
            sensor_network_selector = selector
            break

    assert sensor_network_selector, "failed to retrieve sensor network selector from query target options"

    # grab the first two sensor networks 
    num_networks = 2
    assert isinstance(sensor_network_selector.values, list), "sensor_network_selector values must be a list"
    sensor_network_ids = sensor_network_selector.values[:num_networks] if sensor_network_selector.values else None
    print(f"Selecting sensor network IDs: {sensor_network_ids}")

    assert sensor_network_ids, f"failed to retrieve {num_networks} sensor network IDs from sensor network selector"

    # set up the target with sensor network IDs
    target = ExtraHopTarget(sensor_network_ids=sensor_network_ids)
    assert isinstance(target, ConnectorTargetInterface), "ExtraHopTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_extrahop_telemetry tool
    extrahop_get_telemetry_tool = next(tool for tool in tools if tool.name == "get_extrahop_telemetry")
    extrahop_telemetry_result = await extrahop_get_telemetry_tool.execute()
    extrahop_telemetry = extrahop_telemetry_result.result

    print("Type of returned extrahop_telemetry:", type(extrahop_telemetry))
    print(f"len telemetry: {len(extrahop_telemetry)} telemetry: {str(extrahop_telemetry)[:200]}")

    # Verify that extrahop_telemetry is a list
    assert isinstance(extrahop_telemetry, list), "extrahop_telemetry should be a list"
    assert len(extrahop_telemetry) > 0, "extrahop_telemetry should not be empty"
    
    # Verify structure of each telemetry object
    for telemetry in extrahop_telemetry:
        assert "timestamp" in telemetry, "Each telemetry should have a 'timestamp' field"
        assert "device_id" in telemetry, "Each telemetry should have a 'device_id' field"
        assert "metrics" in telemetry, "Each telemetry should have a 'metrics' field"
        
        # Verify essential ExtraHop telemetry fields
        assert "protocol" in telemetry, "Each telemetry should have a 'protocol' field"
        assert "bytes_in" in telemetry or "bytes_out" in telemetry, "Each telemetry should have traffic volume data"
        
        # Check for additional descriptive fields
        descriptive_fields = ["packets_in", "packets_out", "rtt", "response_time"]
        present_fields = [field for field in descriptive_fields if field in telemetry]
        
        print(f"Telemetry {telemetry.get('device_id', 'unknown')} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first telemetry
        if telemetry == extrahop_telemetry[0]:
            print(f"Example telemetry structure: {telemetry}")

    print(f"Successfully retrieved and validated {len(extrahop_telemetry)} ExtraHop telemetry records")

    return True