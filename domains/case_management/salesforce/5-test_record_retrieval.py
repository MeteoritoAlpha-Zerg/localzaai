# 5-test_record_retrieval.py

async def test_record_retrieval(zerg_state=None):
    """Test retrieving records for a selected Salesforce object"""
    print("Attempting to authenticate using Salesforce connector")

    assert zerg_state, "this test requires valid zerg_state"

    salesforce_username = zerg_state.get("salesforce_username").get("value")
    salesforce_password = zerg_state.get("salesforce_password").get("value")
    salesforce_security_token = zerg_state.get("salesforce_security_token").get("value")
    salesforce_domain = zerg_state.get("salesforce_domain").get("value")

    from connectors.salesforce.config import SalesforceConnectorConfig
    from connectors.salesforce.connector import SalesforceConnector
    from connectors.salesforce.target import SalesforceTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SalesforceConnectorConfig(
        username=salesforce_username,
        password=salesforce_password,
        security_token=salesforce_security_token,
        domain=salesforce_domain
    )
    assert isinstance(config, ConnectorConfig), "SalesforceConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SalesforceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SalesforceConnector should be of type Connector"

    # get query target options
    salesforce_query_target_options = await connector.get_query_target_options()
    assert isinstance(salesforce_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select objects to target
    object_selector = None
    for selector in salesforce_query_target_options.selectors:
        if selector.type == 'objects':  
            object_selector = selector
            break

    assert object_selector, "failed to retrieve object selector from query target options"
    assert isinstance(object_selector.values, list), "object_selector values must be a list"
    assert len(object_selector.values) > 0, "object_selector values should not be empty"
    
    # For testing, we'll use "Account" or the first available object if Account isn't available
    preferred_object = "Account"
    if preferred_object in object_selector.values:
        object_name = preferred_object
    else:
        object_name = object_selector.values[0]
    
    print(f"Selecting object: {object_name}")

    assert object_name, "failed to retrieve object from object selector"

    # set up the target with selected object
    target = SalesforceTarget(objects=[object_name])
    assert isinstance(target, ConnectorTargetInterface), "SalesforceTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the list_salesforce_records tool and execute it with the selected object
    list_records_tool = next(tool for tool in tools if tool.name == "list_salesforce_records")
    records_result = await list_records_tool.execute(object_name=object_name)
    records = records_result.raw_result

    print("Type of returned records:", type(records))
    print(f"Number of records in object {object_name}: {len(records)}")
    
    # Verify that records is a list
    assert isinstance(records, list), "records should be a list"
    # It's possible to have no records in some objects
    if len(records) == 0:
        print(f"No records found in {object_name}. This is valid but consider testing with a different object.")
        return True
    
    # Limit the number of records to check if there are many
    records_to_check = records[:5] if len(records) > 5 else records
    
    # Verify structure of each record object
    for record in records_to_check:
        # Verify essential Salesforce record fields
        assert "Id" in record, "Each record should have an 'Id' field"
        assert "attributes" in record, "Each record should have an 'attributes' field"
        assert "type" in record["attributes"], "The attributes should contain a 'type' field"
        assert record["attributes"]["type"] == object_name, f"Record should belong to the requested object '{object_name}'"
        
        # Check for other record fields - these will vary by object type
        print(f"Record ID: {record['Id']} has the following fields: {', '.join([k for k in record.keys() if k != 'attributes'])}")
        
    # Log the structure of the first record for debugging
    if records_to_check:
        print(f"Example record structure: {records_to_check[0]}")

    print(f"Successfully retrieved and validated {len(records)} records from Salesforce object '{object_name}'")

    return True