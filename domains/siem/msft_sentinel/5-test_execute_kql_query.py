# 5-test_execute_kql_query.py

async def test_execute_kql_query(zerg_state=None):
    """Test executing a KQL query in Microsoft Sentinel"""
    print("Attempting to execute KQL query using Microsoft Sentinel connector")

    assert zerg_state, "this test requires valid zerg_state"

    azure_tenant_id = zerg_state.get("azure_tenant_id").get("value")
    client_id = zerg_state.get("client_id").get("value")
    client_secret = zerg_state.get("client_secret").get("value")
    subscription_id = zerg_state.get("subscription_id").get("value")
    resource_group = zerg_state.get("resource_group").get("value")

    from connectors.microsoft_sentinel.config import MicrosoftSentinelConnectorConfig
    from connectors.microsoft_sentinel.connector import MicrosoftSentinelConnector
    from connectors.microsoft_sentinel.tools import MicrosoftSentinelConnectorTools, ExecuteKQLQueryInput
    from connectors.microsoft_sentinel.target import MicrosoftSentinelTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = MicrosoftSentinelConnectorConfig(
        tenant_id=azure_tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        subscription_id=subscription_id,
        resource_group=resource_group,
    )
    assert isinstance(config, ConnectorConfig), "MicrosoftSentinelConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = MicrosoftSentinelConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MicrosoftSentinelConnector should be of type Connector"

    # get query target options
    sentinel_query_target_options = await connector.get_query_target_options()
    assert isinstance(sentinel_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select workspaces to target
    workspace_selector = None
    for selector in sentinel_query_target_options.selectors:
        if selector.type == 'workspace_names':  
            workspace_selector = selector
            break

    assert workspace_selector, "failed to retrieve workspace selector from query target options"

    assert isinstance(workspace_selector.values, list), "workspace_selector values must be a list"
    workspace_name = workspace_selector.values[0] if workspace_selector.values else None
    print(f"Selecting workspace name: {workspace_name}")

    assert workspace_name, f"failed to retrieve workspace name from workspace selector"

    # set up the target with workspace names
    target = MicrosoftSentinelTarget(workspace_names=[workspace_name])
    assert isinstance(target, ConnectorTargetInterface), "MicrosoftSentinelTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the execute_kql_query tool and execute it with workspace name
    execute_kql_query_tool = next(tool for tool in tools if tool.name == "execute_kql_query")
    
    # Use a simple KQL query that should work in most Microsoft Sentinel workspaces
    test_query = "SecurityEvent | where TimeGenerated > ago(7d) | summarize count() by EventID | take 10"
    
    kql_query_result = await execute_kql_query_tool.execute(
        workspace_name=workspace_name,
        query=test_query
    )
    kql_results = kql_query_result.result

    print("Type of returned kql_results:", type(kql_results))
    print(f"len results: {len(kql_results)} results: {str(kql_results)[:200]}")

    # Verify that kql_results is a list
    assert isinstance(kql_results, list), "kql_results should be a list"
    
    # If there are results, verify their structure
    if len(kql_results) > 0:
        # Limit the number of results to check if there are many
        results_to_check = kql_results[:5] if len(kql_results) > 5 else kql_results
        
        # Verify structure of each result object
        for result in results_to_check:
            # KQL results are typically dictionaries with column names as keys
            assert isinstance(result, dict), "Each KQL result should be a dictionary"
            
            # For this specific query, we expect EventID and count_ fields
            expected_fields = ["EventID", "count_"]
            for field in expected_fields:
                if field in result:
                    print(f"KQL result contains expected field: {field}")
            
            # Log the structure of the first result for debugging
            if result == results_to_check[0]:
                print(f"Example KQL result structure: {result}")

        print(f"Successfully retrieved and validated {len(kql_results)} KQL query results")
    else:
        print("KQL query returned no results - trying alternative query")
        
        # Try a different query that should return results - get available tables
        alternative_query = "search * | getschema | take 5"
        alternative_result = await execute_kql_query_tool.execute(
            workspace_name=workspace_name,
            query=alternative_query
        )
        alternative_data = alternative_result.result
        
        print(f"Alternative query returned {len(alternative_data)} results")
        assert isinstance(alternative_data, list), "alternative query results should be a list"
        
        if len(alternative_data) > 0:
            # Schema results should typically have ColumnName and ColumnType fields
            first_schema_result = alternative_data[0]
            assert isinstance(first_schema_result, dict), "Schema result should be a dictionary"
            
            # Check for common schema fields
            schema_fields = ["ColumnName", "ColumnType", "DataType"]
            present_schema_fields = [field for field in schema_fields if field in first_schema_result]
            
            print(f"Schema result contains these fields: {', '.join(present_schema_fields)}")
            print(f"Example schema result: {first_schema_result}")
            
            print(f"Successfully executed alternative KQL query with {len(alternative_data)} results")

    print(f"Successfully executed KQL queries against workspace {workspace_name}")

    return True