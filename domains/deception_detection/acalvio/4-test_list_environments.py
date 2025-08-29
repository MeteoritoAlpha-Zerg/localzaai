# 4-test_list_environments.py

async def test_list_environments(zerg_state=None):
    """Test Acalvio deception environment enumeration by way of query target options"""
    print("Attempting to authenticate using Acalvio connector")

    assert zerg_state, "this test requires valid zerg_state"

    acalvio_api_url = zerg_state.get("acalvio_api_url").get("value")
    acalvio_api_key = zerg_state.get("acalvio_api_key").get("value")
    acalvio_username = zerg_state.get("acalvio_username").get("value")
    acalvio_password = zerg_state.get("acalvio_password").get("value")
    acalvio_tenant_id = zerg_state.get("acalvio_tenant_id").get("value")

    from connectors.acalvio.config import AcalvioConnectorConfig
    from connectors.acalvio.connector import AcalvioConnector
    from connectors.acalvio.tools import AcalvioConnectorTools
    from connectors.acalvio.target import AcalvioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = AcalvioConnectorConfig(
        api_url=acalvio_api_url,
        api_key=acalvio_api_key,
        username=acalvio_username,
        password=acalvio_password,
        tenant_id=acalvio_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "AcalvioConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = AcalvioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "AcalvioConnectorConfig should be of type ConnectorConfig"

    # get query target options
    acalvio_query_target_options = await connector.get_query_target_options()
    assert isinstance(acalvio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select environments to target
    environment_selector = None
    for selector in acalvio_query_target_options.selectors:
        if selector.type == 'environment_ids':  
            environment_selector = selector
            break

    assert environment_selector, "failed to retrieve environment selector from query target options"

    # grab the first two environments 
    num_environments = 2
    assert isinstance(environment_selector.values, list), "environment_selector values must be a list"
    environment_ids = environment_selector.values[:num_environments] if environment_selector.values else None
    print(f"Selecting environment ids: {environment_ids}")

    assert environment_ids, f"failed to retrieve {num_environments} environment ids from environment selector"

    # set up the target with environment ids
    target = AcalvioTarget(environment_ids=environment_ids)
    assert isinstance(target, ConnectorTargetInterface), "AcalvioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_acalvio_environments tool
    acalvio_get_environments_tool = next(tool for tool in tools if tool.name == "get_acalvio_environments")
    acalvio_environments_result = await acalvio_get_environments_tool.execute()
    acalvio_environments = acalvio_environments_result.result

    print("Type of returned acalvio_environments:", type(acalvio_environments))
    print(f"len environments: {len(acalvio_environments)} environments: {str(acalvio_environments)[:200]}")

    # ensure that acalvio_environments are a list of objects with the id being the environment id
    # and the object having the environment status and other relevant information from the acalvio specification
    # as may be descriptive
    # Verify that acalvio_environments is a list
    assert isinstance(acalvio_environments, list), "acalvio_environments should be a list"
    assert len(acalvio_environments) > 0, "acalvio_environments should not be empty"
    assert len(acalvio_environments) == num_environments, f"acalvio_environments should have {num_environments} entries"
    
    # Verify structure of each environment object
    for environment in acalvio_environments:
        assert "id" in environment, "Each environment should have an 'id' field"
        assert environment["id"] in environment_ids, f"Environment id {environment['id']} is not in the requested environment_ids"
        
        # Verify essential Acalvio environment fields
        # These are common fields in Acalvio environments based on Acalvio API specification
        assert "name" in environment, "Each environment should have a 'name' field"
        assert "status" in environment, "Each environment should have a 'status' field"
        assert "type" in environment, "Each environment should have a 'type' field"
        
        # Check for additional descriptive fields (optional in some Acalvio instances)
        descriptive_fields = ["description", "created_at", "updated_at", "asset_count", "alert_count", "threat_level", "deployment_status"]
        present_fields = [field for field in descriptive_fields if field in environment]
        
        print(f"Environment {environment['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if environment == acalvio_environments[0]:
            print(f"Example environment structure: {environment}")

    print(f"Successfully retrieved and validated {len(acalvio_environments)} Acalvio deception environments")

    return True