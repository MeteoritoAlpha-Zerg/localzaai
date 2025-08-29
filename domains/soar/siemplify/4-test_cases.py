# 4-test_cases.py

async def test_cases(zerg_state=None):
    """Test Siemplify cases enumeration by way of connector tools"""
    print("Attempting to retrieve Siemplify cases using Siemplify connector")

    assert zerg_state, "this test requires valid zerg_state"

    siemplify_server_url = zerg_state.get("siemplify_server_url").get("value")
    siemplify_api_token = zerg_state.get("siemplify_api_token").get("value")
    siemplify_user_name = zerg_state.get("siemplify_user_name").get("value")

    from connectors.siemplify.config import SimemplifyConnectorConfig
    from connectors.siemplify.connector import SimemplifyConnector
    from connectors.siemplify.tools import SimemplifyConnectorTools
    from connectors.siemplify.target import SimemplifyTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = SimemplifyConnectorConfig(
        server_url=siemplify_server_url,
        api_token=siemplify_api_token,
        user_name=siemplify_user_name
    )
    assert isinstance(config, ConnectorConfig), "SimemplifyConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SimemplifyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SimemplifyConnector should be of type Connector"

    # get query target options
    siemplify_query_target_options = await connector.get_query_target_options()
    assert isinstance(siemplify_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select environments to target
    environment_selector = None
    for selector in siemplify_query_target_options.selectors:
        if selector.type == 'environment_ids':  
            environment_selector = selector
            break

    assert environment_selector, "failed to retrieve environment selector from query target options"

    # grab the first two environments 
    num_environments = 2
    assert isinstance(environment_selector.values, list), "environment_selector values must be a list"
    environment_ids = environment_selector.values[:num_environments] if environment_selector.values else None
    print(f"Selecting environment IDs: {environment_ids}")

    assert environment_ids, f"failed to retrieve {num_environments} environment IDs from environment selector"

    # set up the target with environment IDs
    target = SimemplifyTarget(environment_ids=environment_ids)
    assert isinstance(target, ConnectorTargetInterface), "SimemplifyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_siemplify_cases tool
    siemplify_get_cases_tool = next(tool for tool in tools if tool.name == "get_siemplify_cases")
    siemplify_cases_result = await siemplify_get_cases_tool.execute()
    siemplify_cases = siemplify_cases_result.result

    print("Type of returned siemplify_cases:", type(siemplify_cases))
    print(f"len cases: {len(siemplify_cases)} cases: {str(siemplify_cases)[:200]}")

    # Verify that siemplify_cases is a list
    assert isinstance(siemplify_cases, list), "siemplify_cases should be a list"
    assert len(siemplify_cases) > 0, "siemplify_cases should not be empty"
    
    # Verify structure of each case object
    for case in siemplify_cases:
        assert "identifier" in case, "Each case should have an 'identifier' field"
        assert "title" in case, "Each case should have a 'title' field"
        assert "stage" in case, "Each case should have a 'stage' field"
        assert "priority" in case, "Each case should have a 'priority' field"
        assert "creation_time_unix_time_in_ms" in case, "Each case should have a 'creation_time_unix_time_in_ms' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["assigned_user", "environment", "status", "alert_count"]
        present_fields = [field for field in descriptive_fields if field in case]
        
        print(f"Case {case['identifier']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first case
        if case == siemplify_cases[0]:
            print(f"Example case structure: {case}")

    print(f"Successfully retrieved and validated {len(siemplify_cases)} Siemplify cases")

    return True