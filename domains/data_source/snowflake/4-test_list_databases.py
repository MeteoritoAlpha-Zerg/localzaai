# 4-test_list_databases.py

async def test_list_databases(zerg_state=None):
    """Test Snowflake database listing using connector tools"""
    print("Attempting to authenticate using Snowflake connector")

    assert zerg_state, "this test requires valid zerg_state"

    snowflake_account_id = zerg_state.get("snowflake_account_id").get("value")
    snowflake_user = zerg_state.get("snowflake_user").get("value")
    snowflake_password = zerg_state.get("snowflake_password").get("value")

    from connectors.snowflake.config import SnowflakeConnectorConfig
    from connectors.snowflake.connector import SnowflakeConnector
    from connectors.snowflake.tools import SnowflakeConnectorTools
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

    # grab the list_snowflake_databases tool and execute it
    list_databases_tool = next(tool for tool in tools if tool.name == "list_snowflake_databases")
    databases_result = await list_databases_tool.execute()
    databases = databases_result.result

    print("Type of returned databases:", type(databases))
    print(f"Number of databases: {len(databases)}")
    
    # Verify that databases is a list
    assert isinstance(databases, list), "databases should be a list"
    assert len(databases) > 0, "databases should not be empty"
    
    # Limit the number of databases to check if there are many
    databases_to_check = databases[:5] if len(databases) > 5 else databases
    
    # Verify structure of each database object
    for db in databases_to_check:
        # Verify essential Snowflake database fields
        assert "name" in db, "Each database should have a 'name' field"
        assert db["name"] in database_selector.values, f"Database {db['name']} should be in the list of available databases"
        
        # Check for other database details
        expected_fields = ["created_on", "owner"]
        for field in expected_fields:
            assert field in db, f"Database object should contain '{field}' field"
        
        # Optional fields that might be present
        optional_fields = ["comment", "is_current", "is_default", "origin"]
        present_optional = [field for field in optional_fields if field in db]
        
        print(f"Database {db['name']} contains these optional fields: {', '.join(present_optional)}")
        
    # Log the structure of the first database for debugging
    if databases_to_check:
        print(f"Example database structure: {databases_to_check[0]}")

    print(f"Successfully retrieved and validated {len(databases)} Snowflake databases")

    return True