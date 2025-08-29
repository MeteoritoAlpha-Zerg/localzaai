# 6-test_custom_sql_query.py

async def test_custom_sql_query(zerg_state=None):
    """Test Databricks custom SQL query execution for security analysis"""
    print("Testing Databricks custom SQL query execution")

    assert zerg_state, "this test requires valid zerg_state"

    databricks_workspace_url = zerg_state.get("databricks_workspace_url").get("value")
    databricks_access_token = zerg_state.get("databricks_access_token").get("value")
    databricks_cluster_id = zerg_state.get("databricks_cluster_id").get("value")

    from connectors.databricks.config import DatabricksConnectorConfig
    from connectors.databricks.connector import DatabricksConnector
    from connectors.databricks.target import DatabricksTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = DatabricksConnectorConfig(
        workspace_url=databricks_workspace_url,
        access_token=databricks_access_token,
        cluster_id=databricks_cluster_id
    )
    assert isinstance(config, ConnectorConfig), "DatabricksConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = DatabricksConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DatabricksConnector should be of type Connector"

    # get query target options to find available tables
    databricks_query_target_options = await connector.get_query_target_options()
    assert isinstance(databricks_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select table to target for SQL query
    table_selector = None
    for selector in databricks_query_target_options.selectors:
        if selector.type == 'table_names':  
            table_selector = selector
            break

    assert table_selector, "failed to retrieve table selector from query target options"

    assert isinstance(table_selector.values, list), "table_selector values must be a list"
    table_name = table_selector.values[0] if table_selector.values else None
    print(f"Using table for SQL query: {table_name}")

    assert table_name, f"failed to retrieve table name from table selector"

    # set up the target with table name
    target = DatabricksTarget(table_names=[table_name])
    assert isinstance(target, ConnectorTargetInterface), "DatabricksTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the execute_sql_query tool and execute a simple query
    execute_sql_tool = next(tool for tool in tools if tool.name == "execute_sql_query")
    
    # Create a simple SQL query to test functionality
    test_sql_query = f"SELECT * FROM {table_name} LIMIT 10"
    
    sql_result = await execute_sql_tool.execute(sql_query=test_sql_query)
    query_results = sql_result.result

    print("Type of returned query_results:", type(query_results))
    print(f"Query results preview: {str(query_results)[:200]}")

    # Verify that query_results is structured data
    assert query_results is not None, "query_results should not be None"
    
    # Results could be a list of rows or a dictionary with metadata
    if isinstance(query_results, list):
        assert len(query_results) <= 10, "Query should return at most 10 rows due to LIMIT clause"
        
        if len(query_results) > 0:
            # Check first row structure
            first_row = query_results[0]
            assert isinstance(first_row, (dict, list, tuple)), "Each row should be structured data"
            print(f"Example row structure: {first_row}")
            
    elif isinstance(query_results, dict):
        # Results might be wrapped in metadata structure
        expected_keys = ["rows", "data", "results", "columns"]
        has_data_key = any(key in query_results for key in expected_keys)
        assert has_data_key, f"Query results should contain data under one of these keys: {expected_keys}"
        print(f"Query results keys: {list(query_results.keys())}")
    
    else:
        # Results could be in other formats, just ensure it's not empty
        assert str(query_results).strip() != "", "Query results should not be empty"

    print(f"Successfully executed custom SQL query and retrieved results")

    return True