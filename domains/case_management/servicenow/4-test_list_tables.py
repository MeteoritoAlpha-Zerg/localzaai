# 4-test_list_tables.py

async def test_list_tables(zerg_state=None):
    """Test ServiceNow table enumeration by way of query target options"""
    print("Attempting to authenticate using ServiceNow connector")

    assert zerg_state, "this test requires valid zerg_state"

    servicenow_instance_url = zerg_state.get("servicenow_instance_url").get("value")
    servicenow_client_id = zerg_state.get("servicenow_client_id").get("value")
    servicenow_client_secret = zerg_state.get("servicenow_client_secret").get("value")
    servicenow_username = zerg_state.get("servicenow_username").get("value")
    servicenow_password = zerg_state.get("servicenow_username").get("value")

    from connectors.servicenow.config import ServiceNowConnectorConfig
    from connectors.servicenow.connector import ServiceNowConnector
    from connectors.servicenow.tools import ServiceNowConnectorTools
    from connectors.servicenow.target import ServiceNowTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = ServiceNowConnectorConfig(
        instance_url=servicenow_instance_url,
        client_id=servicenow_client_id,
        client_secret=servicenow_client_secret,
        servicenow_username=servicenow_username,
        servicenow_password=servicenow_password
    )
    assert isinstance(config, ConnectorConfig), "ServiceNowConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ServiceNowConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ServiceNowConnector should be of type Connector"

    # get query target options
    servicenow_query_target_options = await connector.get_query_target_options()
    assert isinstance(servicenow_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select tables to target
    table_selector = None
    for selector in servicenow_query_target_options.selectors:
        if selector.type == 'table_names':  # Assuming 'table_names' is the type for ServiceNow tables
            table_selector = selector
            break

    assert table_selector, "failed to retrieve table selector from query target options"

    # grab the first two tables 
    num_tables = 2
    assert isinstance(table_selector.values, list), "table_selector values must be a list"
    table_names = table_selector.values[:num_tables] if table_selector.values else None
    print(f"Selecting table names: {table_names}")

    assert table_names, f"failed to retrieve {num_tables} table names from table selector"

    # set up the target with table names
    target = ServiceNowTarget(table_names=table_names)
    assert isinstance(target, ConnectorTargetInterface), "ServiceNowTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_servicenow_tables tool
    servicenow_get_tables_tool = next(tool for tool in tools if tool.name == "get_servicenow_tables")
    servicenow_tables_result = await servicenow_get_tables_tool.execute()
    servicenow_tables = servicenow_tables_result.result

    print("Type of returned servicenow_tables:", type(servicenow_tables))
    print(f"len tables: {len(servicenow_tables)} tables: {str(servicenow_tables)[:200]}")

    # Verify that servicenow_tables is a list
    assert isinstance(servicenow_tables, list), "servicenow_tables should be a list"
    assert len(servicenow_tables) > 0, "servicenow_tables should not be empty"
    assert len(servicenow_tables) == num_tables, f"servicenow_tables should have {num_tables} entries"
    
    # Verify structure of each table object
    for table in servicenow_tables:
        assert "name" in table, "Each table should have a 'name' field"
        assert table["name"] in table_names, f"Table name {table['name']} is not in the requested table_names"
        
        # Verify essential ServiceNow table fields
        assert "sys_id" in table, "Each table should have a 'sys_id' field"
        assert "label" in table, "Each table should have a 'label' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["description", "element_count", "access", "display_name"]
        present_fields = [field for field in descriptive_fields if field in table]
        
        print(f"Table {table['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if table == servicenow_tables[0]:
            print(f"Example table structure: {table}")

    print(f"Successfully retrieved and validated {len(servicenow_tables)} ServiceNow tables")

    return True