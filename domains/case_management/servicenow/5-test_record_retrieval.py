# 5-test_record_retrieval.py

async def test_record_retrieval(zerg_state=None):
    """Test ServiceNow record retrieval by way of query target options"""
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

    # grab the first table
    assert isinstance(table_selector.values, list), "table_selector values must be a list"
    table_name = table_selector.values[0] if table_selector.values else None
    print(f"Selecting table name: {table_name}")

    assert table_name, "failed to retrieve table name from table selector"

    # set up the target with table name
    target = ServiceNowTarget(table_names=[table_name])
    assert isinstance(target, ConnectorTargetInterface), "ServiceNowTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_servicenow_records tool
    servicenow_get_records_tool = next(tool for tool in tools if tool.name == "get_servicenow_records")
    servicenow_records_result = await servicenow_get_records_tool.execute(table_name=table_name)
    servicenow_records = servicenow_records_result.result

    print("Type of returned servicenow_records:", type(servicenow_records))
    print(f"len records: {len(servicenow_records)} records: {str(servicenow_records)[:200]}")

    # Verify that servicenow_records is a list
    assert isinstance(servicenow_records, list), "servicenow_records should be a list"
    assert len(servicenow_records) > 0, "servicenow_records should not be empty"
    
    # Verify structure of first record
    first_record = servicenow_records[0]
    assert "sys_id" in first_record, "Each record should have a 'sys_id' field"
    
    # Get record identifiers for logging
    record_id = first_record.get('sys_id')
    record_name = first_record.get('number', first_record.get('name', f"Record {record_id}"))
    
    # Check for common ServiceNow record fields
    common_fields = ["sys_created_on", "sys_updated_on", "sys_created_by", "sys_updated_by"]
    present_fields = [field for field in common_fields if field in first_record]
    
    print(f"Record {record_name} contains these common fields: {', '.join(present_fields)}")
    
    # Additional fields that might be present based on table type
    table_specific_fields = [field for field in first_record.keys() 
                             if field not in common_fields and field != "sys_id"]
    print(f"Record-specific fields: {', '.join(table_specific_fields[:5])}{'...' if len(table_specific_fields) > 5 else ''}")
    
    # Log example record
    print(f"Example record: {first_record}")

    print(f"Successfully retrieved and validated ServiceNow records for table {table_name}")

    return True