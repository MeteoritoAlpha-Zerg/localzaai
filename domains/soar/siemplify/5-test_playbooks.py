# 5-test_playbooks.py

async def test_playbooks(zerg_state=None):
    """Test Siemplify playbook and automation execution"""
    print("Attempting to execute playbooks using Siemplify connector")

    assert zerg_state, "this test requires valid zerg_state"

    siemplify_server_url = zerg_state.get("siemplify_server_url").get("value")
    siemplify_api_token = zerg_state.get("siemplify_api_token").get("value")
    siemplify_user_name = zerg_state.get("siemplify_user_name").get("value")

    from connectors.siemplify.config import SimemplifyConnectorConfig
    from connectors.siemplify.connector import SimemplifyConnector
    from connectors.siemplify.tools import SimemplifyConnectorTools, ExecutePlaybookInput
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

    assert isinstance(environment_selector.values, list), "environment_selector values must be a list"
    environment_id = environment_selector.values[0] if environment_selector.values else None
    print(f"Selecting environment ID: {environment_id}")

    assert environment_id, f"failed to retrieve environment ID from environment selector"

    # set up the target with environment ID
    target = SimemplifyTarget(environment_ids=[environment_id])
    assert isinstance(target, ConnectorTargetInterface), "SimemplifyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the execute_playbook tool and execute it
    execute_playbook_tool = next(tool for tool in tools if tool.name == "execute_playbook")
    playbook_result = await execute_playbook_tool.execute(
        case_id="12345",
        playbook_name="Test Enrichment Playbook"
    )
    playbook_data = playbook_result.result

    print("Type of returned playbook_data:", type(playbook_data))
    print(f"Playbook execution result: {str(playbook_data)[:200]}")

    # Verify that playbook_data is a dictionary
    assert isinstance(playbook_data, dict), "playbook_data should be a dictionary"
    
    # Verify essential playbook execution fields
    assert "execution_id" in playbook_data, "Playbook result should have 'execution_id' field"
    assert "status" in playbook_data, "Playbook result should have 'status' field"
    
    # Test action execution if available
    if "execute_action" in [tool.name for tool in tools]:
        execute_action_tool = next(tool for tool in tools if tool.name == "execute_action")
        action_result = await execute_action_tool.execute(
            case_id="12345",
            action_name="Ping",
            parameters={"host": "8.8.8.8"}
        )
        action_data = action_result.result
        
        if action_data:
            assert isinstance(action_data, dict), "Action result should be a dictionary"
            
            action_fields = ["action_id", "status", "result_value"]
            present_fields = [field for field in action_fields if field in action_data]
            
            print(f"Action execution contains these fields: {', '.join(present_fields)}")
    
    # Test entity enrichment if available
    if "enrich_entities" in [tool.name for tool in tools]:
        enrich_entities_tool = next(tool for tool in tools if tool.name == "enrich_entities")
        enrichment_result = await enrich_entities_tool.execute(
            case_id="12345",
            entity_identifiers=["192.168.1.1", "example.com"]
        )
        enrichment_data = enrichment_result.result
        
        if enrichment_data:
            assert isinstance(enrichment_data, list), "Entity enrichment result should be a list"
            print(f"Entity enrichment completed for {len(enrichment_data)} entities")

    print(f"Successfully executed playbook automation")

    return True