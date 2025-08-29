async def test_record_content_retrieval(zerg_state=None):
    """Test ServiceNow specific record content retrieval by record ID"""
    print("Attempting to retrieve detailed content from a specific ServiceNow record")

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
        if selector.type == 'table_names':
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

    # First, get a record ID to test with
    # grab the get_servicenow_records tool
    servicenow_get_records_tool = next(tool for tool in tools if tool.name == "get_servicenow_records")
    servicenow_records_result = await servicenow_get_records_tool.execute(table_name=table_name)
    servicenow_records = servicenow_records_result.result

    assert isinstance(servicenow_records, list), "servicenow_records should be a list"
    assert len(servicenow_records) > 0, "servicenow_records should not be empty"
    
    # Get a record ID to test with
    first_record = servicenow_records[0]
    record_id = first_record.get('sys_id')
    record_name = first_record.get('number', first_record.get('name', f"Record {record_id}"))
    
    print(f"Testing content retrieval for record: {record_name} (ID: {record_id})")
    assert record_id, "Failed to retrieve a valid record ID for testing"

    # Now, get the detailed content for this specific record
    # Find the get_servicenow_record_content tool (or similar)
    servicenow_get_record_content_tool = next(tool for tool in tools if tool.name == "get_servicenow_record_content")
    
    # Execute the tool with the record_id parameter
    record_content_result = await servicenow_get_record_content_tool.execute(
        table_name=table_name,
        record_id=record_id
    )
    record_content = record_content_result.result
    
    # Verify the content structure
    assert record_content, "Record content should not be empty"
    assert isinstance(record_content, dict), "Record content should be a dictionary"
    
    # Check that the returned content has the correct record ID
    assert "sys_id" in record_content, "Record content should include sys_id field"
    assert record_content["sys_id"] == record_id, "Record content sys_id should match requested record_id"
    
    # Verify essential fields are present
    assert "sys_created_on" in record_content, "Record content should include sys_created_on field"
    assert "sys_updated_on" in record_content, "Record content should include sys_updated_on field"
    
    # Check for detailed content fields based on table type
    # Count the number of fields to ensure we got detailed content
    field_count = len(record_content.keys())
    print(f"Record content contains {field_count} fields")
    assert field_count > 5, "Record content should contain multiple fields with detailed information"
    
    # Print a sample of the content fields (but not all to avoid clutter)
    important_fields = [key for key in record_content.keys() if key not in 
                       ["sys_id", "sys_created_on", "sys_updated_on", "sys_created_by", "sys_updated_by"]]
    sample_fields = important_fields[:5]
    
    print("Sample content fields:")
    for field in sample_fields:
        print(f"  - {field}: {record_content[field]}")
    
    # Check if content-specific fields are present based on table type
    if table_name == "incident":
        assert "short_description" in record_content, "Incident should have short_description field"
        assert "description" in record_content, "Incident should have description field"
        assert "priority" in record_content, "Incident should have priority field"
    elif table_name == "change_request":
        assert "short_description" in record_content, "Change request should have short_description field"
        assert "risk_impact_analysis" in record_content, "Change request should have risk_impact_analysis field"
    elif table_name == "problem":
        assert "short_description" in record_content, "Problem should have short_description field"
        assert "known_error" in record_content, "Problem should have known_error field"
    
    print(f"Successfully retrieved and validated detailed content for {table_name} record {record_id}")
    
    return True