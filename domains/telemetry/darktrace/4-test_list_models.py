# 4-test_list_models.py

async def test_list_models(zerg_state=None):
    """Test Darktrace model and device enumeration by way of connector tools"""
    print("Attempting to authenticate using Darktrace connector")

    assert zerg_state, "this test requires valid zerg_state"

    darktrace_url = zerg_state.get("darktrace_url").get("value")
    darktrace_public_token = zerg_state.get("darktrace_public_token").get("value")
    darktrace_private_token = zerg_state.get("darktrace_private_token").get("value")

    from connectors.darktrace.config import DarktraceConnectorConfig
    from connectors.darktrace.connector import DarktraceConnector
    from connectors.darktrace.tools import DarktraceConnectorTools
    from connectors.darktrace.target import DarktraceTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = DarktraceConnectorConfig(
        url=darktrace_url,
        public_token=darktrace_public_token,
        private_token=darktrace_private_token,
    )
    assert isinstance(config, ConnectorConfig), "DarktraceConnectorConfig should be of type ConnectorConfig"

    connector = DarktraceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DarktraceConnector should be of type Connector"

    darktrace_query_target_options = await connector.get_query_target_options()
    assert isinstance(darktrace_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    model_selector = None
    for selector in darktrace_query_target_options.selectors:
        if selector.type == 'model_uuids':  
            model_selector = selector
            break

    assert model_selector, "failed to retrieve model selector from query target options"

    num_models = 2
    assert isinstance(model_selector.values, list), "model_selector values must be a list"
    model_uuids = model_selector.values[:num_models] if model_selector.values else None
    print(f"Selecting model UUIDs: {model_uuids}")

    assert model_uuids, f"failed to retrieve {num_models} model UUIDs from model selector"

    target = DarktraceTarget(model_uuids=model_uuids)
    assert isinstance(target, ConnectorTargetInterface), "DarktraceTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    darktrace_get_models_tool = next(tool for tool in tools if tool.name == "get_darktrace_models")
    darktrace_models_result = await darktrace_get_models_tool.execute()
    darktrace_models = darktrace_models_result.result

    print("Type of returned darktrace_models:", type(darktrace_models))
    print(f"len models: {len(darktrace_models)} models: {str(darktrace_models)[:200]}")

    assert isinstance(darktrace_models, list), "darktrace_models should be a list"
    assert len(darktrace_models) > 0, "darktrace_models should not be empty"
    assert len(darktrace_models) == num_models, f"darktrace_models should have {num_models} entries"
    
    for model in darktrace_models:
        assert "uuid" in model, "Each model should have a 'uuid' field"
        assert model["uuid"] in model_uuids, f"Model UUID {model['uuid']} is not in the requested model_uuids"
        assert "name" in model, "Each model should have a 'name' field"
        assert "category" in model, "Each model should have a 'category' field"
        
        descriptive_fields = ["description", "priority", "version", "active", "tags", "created"]
        present_fields = [field for field in descriptive_fields if field in model]
        
        print(f"Model {model['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        if model == darktrace_models[0]:
            print(f"Example model structure: {model}")

    print(f"Successfully retrieved and validated {len(darktrace_models)} Darktrace models")

    # Test devices as well
    get_darktrace_devices_tool = next(tool for tool in tools if tool.name == "get_darktrace_devices")
    darktrace_devices_result = await get_darktrace_devices_tool.execute(limit=10)
    darktrace_devices = darktrace_devices_result.result

    print("Type of returned darktrace_devices:", type(darktrace_devices))

    assert isinstance(darktrace_devices, list), "darktrace_devices should be a list"
    
    if len(darktrace_devices) > 0:
        devices_to_check = darktrace_devices[:3] if len(darktrace_devices) > 3 else darktrace_devices
        
        for device in devices_to_check:
            assert "did" in device, "Each device should have a 'did' field"
            assert "ip" in device, "Each device should have an 'ip' field"
            
            device_fields = ["hostname", "mac", "vendor", "os", "devicelabel", "firstSeen", "lastSeen"]
            present_device_fields = [field for field in device_fields if field in device]
            
            print(f"Device {device['ip']} contains these fields: {', '.join(present_device_fields)}")
        
        print(f"Successfully retrieved and validated {len(darktrace_devices)} Darktrace devices")

    return True