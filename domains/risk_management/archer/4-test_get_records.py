# 4-test_get_records.py

async def test_get_records(zerg_state=None):
    """Test RSA Archer GRC records retrieval"""
    print("Testing RSA Archer GRC records retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    rsa_archer_api_url = zerg_state.get("rsa_archer_api_url").get("value")
    rsa_archer_username = zerg_state.get("rsa_archer_username").get("value")
    rsa_archer_password = zerg_state.get("rsa_archer_password").get("value")
    rsa_archer_instance_name = zerg_state.get("rsa_archer_instance_name").get("value")

    from connectors.rsa_archer.config import RSAArcherConnectorConfig
    from connectors.rsa_archer.connector import RSAArcherConnector
    from connectors.rsa_archer.target import RSAArcherTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = RSAArcherConnectorConfig(
        api_url=rsa_archer_api_url,
        username=rsa_archer_username,
        password=rsa_archer_password,
        instance_name=rsa_archer_instance_name
    )
    assert isinstance(config, ConnectorConfig), "RSAArcherConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = RSAArcherConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RSAArcherConnector should be of type Connector"

    # get query target options
    rsa_archer_query_target_options = await connector.get_query_target_options()
    assert isinstance(rsa_archer_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select applications for records retrieval
    application_selector = None
    for selector in rsa_archer_query_target_options.selectors:
        if selector.type == 'applications':  
            application_selector = selector
            break

    assert application_selector, "failed to retrieve application selector from query target options"
    assert isinstance(application_selector.values, list), "application_selector values must be a list"
    
    # Find the first available application
    selected_application = application_selector.values[0] if application_selector.values else None
    assert selected_application, "No applications available for records retrieval"
    print(f"Selecting application: {selected_application}")

    # set up the target with selected application
    target = RSAArcherTarget(applications=[selected_application])
    assert isinstance(target, ConnectorTargetInterface), "RSAArcherTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_rsa_archer_records tool
    rsa_archer_get_records_tool = next(tool for tool in tools if tool.name == "get_rsa_archer_records")
    records_result = await rsa_archer_get_records_tool.execute(application=selected_application)
    records_data = records_result.result

    print("Type of returned records data:", type(records_data))
    print(f"Records count: {len(records_data)} sample: {str(records_data)[:200]}")

    # Verify that records_data is a list
    assert isinstance(records_data, list), "Records data should be a list"
    assert len(records_data) > 0, "Records data should not be empty"
    
    # Limit the number of records to check if there are many
    records_to_check = records_data[:5] if len(records_data) > 5 else records_data
    
    # Verify structure of each record entry
    for record in records_to_check:
        # Verify essential record fields per RSA Archer API specification
        assert "Id" in record or "id" in record, "Each record should have an 'Id' or 'id' field"
        
        # Get the record ID (RSA Archer uses capitalized field names)
        record_id = record.get("Id") or record.get("id")
        assert record_id, "Record ID should not be empty"
        
        # Check for additional record fields per RSA Archer specification
        record_fields = ["Title", "Status", "CreatedDate", "ModifiedDate", "Fields", "TrackingId"]
        present_fields = [field for field in record_fields if field in record]
        
        print(f"Record {record_id} contains: {', '.join(present_fields)}")
        
        # If Fields are present, validate structure (RSA Archer's field system)
        if "Fields" in record:
            fields = record["Fields"]
            assert isinstance(fields, (dict, list)), "Fields should be a dictionary or list"
            if isinstance(fields, dict):
                # Check that field data is present
                assert len(fields) > 0, "Fields dictionary should not be empty"
            elif isinstance(fields, list):
                # Check that field list contains field objects
                for field in fields:
                    assert isinstance(field, dict), "Each field should be a dictionary"
                    assert "Id" in field or "FieldId" in field, "Each field should have an Id or FieldId"
        
        # If Status is present, validate it's not empty
        if "Status" in record:
            status = record["Status"]
            assert status, "Status should not be empty"
        
        # If Title is present, validate it's not empty
        if "Title" in record:
            title = record["Title"]
            assert title and title.strip(), "Title should not be empty"
        
        # If CreatedDate is present, validate it's not empty
        if "CreatedDate" in record:
            created_date = record["CreatedDate"]
            assert created_date, "CreatedDate should not be empty"
        
        # If TrackingId is present, validate it's not empty
        if "TrackingId" in record:
            tracking_id = record["TrackingId"]
            assert tracking_id, "TrackingId should not be empty"
        
        # Log the structure of the first record for debugging
        if record == records_to_check[0]:
            print(f"Example record structure: {record}")

    print(f"Successfully retrieved and validated {len(records_data)} RSA Archer records")

    return True