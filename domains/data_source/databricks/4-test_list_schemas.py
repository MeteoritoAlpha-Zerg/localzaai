# 4-test_list_schemas.py

async def test_list_schemas(zerg_state=None):
    """Test Databricks schema and table enumeration by way of connector tools"""
    print("Testing Databricks schema and table listing")

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

    # select schemas to target
    schema_selector = None
    for selector in databricks_query_target_options.selectors:
        if selector.type == 'schema_names':  
            schema_selector = selector
            break

    assert schema_selector, "failed to retrieve schema selector from query target options"

    # grab the first two schemas 
    num_schemas = 2
    assert isinstance(schema_selector.values, list), "schema_selector values must be a list"
    schema_names = schema_selector.values[:num_schemas] if schema_selector.values else None
    print(f"Selecting schema names: {schema_names}")

    assert schema_names, f"failed to retrieve {num_schemas} schema names from schema selector"

    # set up the target with schema names
    target = DatabricksTarget(schema_names=schema_names)
    assert isinstance(target, ConnectorTargetInterface), "DatabricksTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_databricks_schemas tool
    databricks_get_schemas_tool = next(tool for tool in tools if tool.name == "get_databricks_schemas")
    databricks_schemas_result = await databricks_get_schemas_tool.execute()
    databricks_schemas = databricks_schemas_result.result

    print("Type of returned databricks_schemas:", type(databricks_schemas))
    print(f"len schemas: {len(databricks_schemas)} schemas: {str(databricks_schemas)[:200]}")

    # Verify that databricks_schemas is a list
    assert isinstance(databricks_schemas, list), "databricks_schemas should be a list"
    assert len(databricks_schemas) > 0, "databricks_schemas should not be empty"
    assert len(databricks_schemas) == num_schemas, f"databricks_schemas should have {num_schemas} entries"
    
    # Verify structure of each schema object
    for schema in databricks_schemas:
        assert "name" in schema, "Each schema should have a 'name' field"
        assert schema["name"] in schema_names, f"Schema name {schema['name']} is not in the requested schema_names"
        
        # Verify essential schema fields
        assert "catalog" in schema, "Each schema should have a 'catalog' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["comment", "owner", "tables"]
        present_fields = [field for field in descriptive_fields if field in schema]
        
        print(f"Schema {schema['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first schema
        if schema == databricks_schemas[0]:
            print(f"Example schema structure: {schema}")

    print(f"Successfully retrieved and validated {len(databricks_schemas)} Databricks schemas")

    return True