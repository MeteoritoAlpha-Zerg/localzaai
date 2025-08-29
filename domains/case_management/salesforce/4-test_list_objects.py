# 4-test_list_objects.py

async def test_list_objects(zerg_state=None):
    """Test Salesforce object listing using connector tools"""
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
    
    object_name = object_selector.values[0] if object_selector.values else None
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

    # grab the list_salesforce_objects tool and execute it
    list_objects_tool = next(tool for tool in tools if tool.name == "list_salesforce_objects")
    objects_result = await list_objects_tool.execute()
    objects = objects_result.raw_result

    print("Type of returned objects:", type(objects))
    print(f"Number of objects: {len(objects)}")
    
    # Verify that objects is a list
    assert isinstance(objects, list), "objects should be a list"
    assert len(objects) > 0, "objects should not be empty"
    
    # Limit the number of objects to check if there are many
    objects_to_check = objects[:5] if len(objects) > 5 else objects
    
    # Verify structure of each object object
    for obj in objects_to_check:
        # Verify essential Salesforce object fields
        assert "name" in obj, "Each object should have a 'name' field"
        assert obj["name"] in object_selector.values, f"Object {obj['name']} should be in the list of available objects"
        
        # Check for other object details
        expected_fields = ["label", "keyPrefix", "custom"]
        for field in expected_fields:
            assert field in obj, f"Object should contain '{field}' field"
        
        # Optional fields that might be present
        optional_fields = ["createable", "updateable", "deletable", "queryable", "searchable", "description"]
        present_optional = [field for field in optional_fields if field in obj]
        
        print(f"Object {obj['name']} contains these optional fields: {', '.join(present_optional)}")
        
    # Log the structure of the first object for debugging
    if objects_to_check:
        print(f"Example object structure: {objects_to_check[0]}")

    print(f"Successfully retrieved and validated {len(objects)} Salesforce objects")

    return True