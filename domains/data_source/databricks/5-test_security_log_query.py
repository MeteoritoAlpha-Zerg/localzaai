# 5-test_security_log_query.py

async def test_security_log_query(zerg_state=None):
    """Test Databricks security log querying capabilities"""
    print("Testing Databricks security log query")

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

    # get query target options
    databricks_query_target_options = await connector.get_query_target_options()
    assert isinstance(databricks_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select table to target
    table_selector = None
    for selector in databricks_query_target_options.selectors:
        if selector.type == 'table_names':  
            table_selector = selector
            break

    assert table_selector, "failed to retrieve table selector from query target options"

    assert isinstance(table_selector.values, list), "table_selector values must be a list"
    table_name = table_selector.values[0] if table_selector.values else None
    print(f"Selecting table name: {table_name}")

    assert table_name, f"failed to retrieve table name from table selector"

    # set up the target with table name
    target = DatabricksTarget(table_names=[table_name])
    assert isinstance(target, ConnectorTargetInterface), "DatabricksTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the query_security_logs tool and execute it with table name
    query_security_logs_tool = next(tool for tool in tools if tool.name == "query_security_logs")
    security_logs_result = await query_security_logs_tool.execute(table_name=table_name)
    security_logs = security_logs_result.result

    print("Type of returned security_logs:", type(security_logs))
    print(f"len logs: {len(security_logs)} logs: {str(security_logs)[:200]}")

    # Verify that security_logs is a list
    assert isinstance(security_logs, list), "security_logs should be a list"
    assert len(security_logs) > 0, "security_logs should not be empty"
    
    # Limit the number of logs to check if there are many
    logs_to_check = security_logs[:5] if len(security_logs) > 5 else security_logs
    
    # Verify structure of each log entry
    for log in logs_to_check:
        # Verify log is a dictionary/object
        assert isinstance(log, dict), "Each log entry should be a dictionary"
        
        # Check for common security log fields
        common_fields = ["timestamp", "event_type", "source"]
        present_common = [field for field in common_fields if field in log]
        
        # At least one common field should be present
        assert len(present_common) > 0, f"Log entry should contain at least one common field: {common_fields}"
        
        print(f"Log entry contains these common fields: {', '.join(present_common)}")
        
        # Log the structure of the first log entry for debugging
        if log == logs_to_check[0]:
            print(f"Example log entry structure: {log}")

    print(f"Successfully retrieved and validated {len(security_logs)} security log entries")

    return True