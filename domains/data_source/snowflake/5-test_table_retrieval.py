# 5-test_table_retrieval.py

async def test_table_retrieval(zerg_state=None):
    """Test retrieving tables for a selected Snowflake database"""
    print("Attempting to authenticate using Snowflake connector")

    assert zerg_state, "this test requires valid zerg_state"

    snowflake_account_id = zerg_state.get("snowflake_account_id").get("value")
    snowflake_user = zerg_state.get("snowflake_user").get("value")
    snowflake_password = zerg_state.get("snowflake_password").get("value")

    from connectors.snowflake.config import SnowflakeConnectorConfig
    from connectors.snowflake.connector import SnowflakeConnector
    from connectors.snowflake.target import SnowflakeTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SnowflakeConnectorConfig(
        account_id=snowflake_account_id,
        user=snowflake_user,
        password=snowflake_password
    )
    assert isinstance(config, ConnectorConfig), "SnowflakeConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SnowflakeConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SnowflakeConnector should be of type Connector"

    # get query target options
    snowflake_query_target_options = await connector.get_query_target_options()
    assert isinstance(snowflake_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select databases to target
    database_selector = None
    for selector in snowflake_query_target_options.selectors:
        if selector.type == 'databases':  
            database_selector = selector
            break

    assert database_selector, "failed to retrieve database selector from query target options"
    assert isinstance(database_selector.values, list), "database_selector values must be a list"
    assert len(database_selector.values) > 0, "database_selector values should not be empty"
    
    database = database_selector.values[0] if database_selector.values else None
    print(f"Selecting database: {database}")

    assert database, "failed to retrieve database from database selector"

    # set up the target with selected database
    target = SnowflakeTarget(databases=[database])
    assert isinstance(target, ConnectorTargetInterface), "SnowflakeTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the list_snowflake_tables tool and execute it with the selected database
    list_tables_tool = next(tool for tool in tools if tool.name == "list_snowflake_tables")
    tables_result = await list_tables_tool.execute(database=database)
    tables = tables_result.result

    print("Type of returned tables:", type(tables))
    print(f"Number of tables in database {database}: {len(tables)}")
    
    # Verify that tables is a list
    assert isinstance(tables, list), "tables should be a list"
    assert len(tables) > 0, "tables should not be empty"
    
    # Limit the number of tables to check if there are many
    tables_to_check = tables[:5] if len(tables) > 5 else tables
    
    # Verify structure of each table object
    for table in tables_to_check:
        # Verify essential Snowflake table fields
        assert "name" in table, "Each table should have a 'name' field"
        assert "database" in table, "Each table should have a 'database' field"
        assert table["database"] == database, f"Table {table['name']} should belong to the requested database '{database}'"
        
        # Check for other table details
        expected_fields = ["schema", "created_on", "owner"]
        for field in expected_fields:
            assert field in table, f"Table object should contain '{field}' field"
        
        # Optional fields that might be present
        optional_fields = ["comment", "table_type", "bytes", "row_count", "retention_time"]
        present_optional = [field for field in optional_fields if field in table]
        
        print(f"Table {table['name']} contains these optional fields: {', '.join(present_optional)}")
        
    # Log the structure of the first table for debugging
    if tables_to_check:
        print(f"Example table structure: {tables_to_check[0]}")

    print(f"Successfully retrieved and validated {len(tables)} tables from Snowflake database '{database}'")

    return True