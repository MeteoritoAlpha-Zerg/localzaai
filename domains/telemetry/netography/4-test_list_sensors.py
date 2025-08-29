# 4-test_list_sensors.py

async def test_list_sensors(zerg_state=None):
    """Test Netography sensor enumeration by way of connector tools"""
    print("Testing Netography sensor listing")

    assert zerg_state, "this test requires valid zerg_state"

    netography_api_token = zerg_state.get("netography_api_token").get("value")
    netography_base_url = zerg_state.get("netography_base_url").get("value")
    netography_tenant_id = zerg_state.get("netography_tenant_id").get("value")

    from connectors.netography.config import NetographyConnectorConfig
    from connectors.netography.connector import NetographyConnector
    from connectors.netography.target import NetographyTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = NetographyConnectorConfig(
        api_token=netography_api_token,
        base_url=netography_base_url,
        tenant_id=netography_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "NetographyConnectorConfig should be of type ConnectorConfig"

    connector = NetographyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "NetographyConnector should be of type Connector"

    netography_query_target_options = await connector.get_query_target_options()
    assert isinstance(netography_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    sensor_selector = None
    for selector in netography_query_target_options.selectors:
        if selector.type == 'sensor_ids':  
            sensor_selector = selector
            break

    assert sensor_selector, "failed to retrieve sensor selector from query target options"

    num_sensors = 2
    assert isinstance(sensor_selector.values, list), "sensor_selector values must be a list"
    sensor_ids = sensor_selector.values[:num_sensors] if sensor_selector.values else None
    print(f"Selecting sensor IDs: {sensor_ids}")

    assert sensor_ids, f"failed to retrieve {num_sensors} sensor IDs from sensor selector"

    target = NetographyTarget(sensor_ids=sensor_ids)
    assert isinstance(target, ConnectorTargetInterface), "NetographyTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    netography_get_sensors_tool = next(tool for tool in tools if tool.name == "get_netography_sensors")
    netography_sensors_result = await netography_get_sensors_tool.execute()
    netography_sensors = netography_sensors_result.result

    print("Type of returned netography_sensors:", type(netography_sensors))
    print(f"len sensors: {len(netography_sensors)} sensors: {str(netography_sensors)[:200]}")

    assert isinstance(netography_sensors, list), "netography_sensors should be a list"
    assert len(netography_sensors) > 0, "netography_sensors should not be empty"
    assert len(netography_sensors) == num_sensors, f"netography_sensors should have {num_sensors} entries"
    
    for sensor in netography_sensors:
        assert "id" in sensor, "Each sensor should have an 'id' field"
        assert sensor["id"] in sensor_ids, f"Sensor ID {sensor['id']} is not in the requested sensor_ids"
        assert "name" in sensor, "Each sensor should have a 'name' field"
        assert "status" in sensor, "Each sensor should have a 'status' field"
        
        descriptive_fields = ["location", "type", "version", "last_seen", "data_sources"]
        present_fields = [field for field in descriptive_fields if field in sensor]
        
        print(f"Sensor {sensor['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        if "status" in sensor:
            valid_statuses = ["online", "offline", "maintenance"]
            assert sensor["status"] in valid_statuses, f"Sensor status should be valid"
        
        if "type" in sensor:
            valid_types = ["network", "endpoint", "cloud", "hybrid"]
            assert sensor["type"] in valid_types, f"Sensor type should be valid"
        
        if sensor == netography_sensors[0]:
            print(f"Example sensor structure: {sensor}")

    print(f"Successfully retrieved and validated {len(netography_sensors)} Netography sensors")

    return True