# 5-test_stix_object_retrieval.py

async def test_stix_object_retrieval(zerg_state=None):
    """Test STIX object retrieval from TAXII collections"""
    print("Testing STIX object retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    taxii_server_url = zerg_state.get("taxii_server_url").get("value")
    taxii_username = zerg_state.get("taxii_username").get("value")
    taxii_password = zerg_state.get("taxii_password").get("value")

    from connectors.stix_taxii.config import STIXTAXIIConnectorConfig
    from connectors.stix_taxii.connector import STIXTAXIIConnector
    from connectors.stix_taxii.target import STIXTAXIITarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = STIXTAXIIConnectorConfig(
        server_url=taxii_server_url,
        username=taxii_username,
        password=taxii_password
    )
    assert isinstance(config, ConnectorConfig), "STIXTAXIIConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = STIXTAXIIConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "STIXTAXIIConnector should be of type Connector"

    # get query target options
    stix_taxii_query_target_options = await connector.get_query_target_options()
    assert isinstance(stix_taxii_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select collection to target
    collection_selector = None
    for selector in stix_taxii_query_target_options.selectors:
        if selector.type == 'collection_ids':  
            collection_selector = selector
            break

    assert collection_selector, "failed to retrieve collection selector from query target options"

    assert isinstance(collection_selector.values, list), "collection_selector values must be a list"
    collection_id = collection_selector.values[0] if collection_selector.values else None
    print(f"Selecting collection ID: {collection_id}")

    assert collection_id, f"failed to retrieve collection ID from collection selector"

    # set up the target with collection ID
    target = STIXTAXIITarget(collection_ids=[collection_id])
    assert isinstance(target, ConnectorTargetInterface), "STIXTAXIITarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_stix_objects tool and execute it with collection ID
    get_stix_objects_tool = next(tool for tool in tools if tool.name == "get_stix_objects")
    stix_objects_result = await get_stix_objects_tool.execute(collection_id=collection_id)
    stix_objects = stix_objects_result.result

    print("Type of returned stix_objects:", type(stix_objects))
    print(f"len objects: {len(stix_objects)} objects: {str(stix_objects)[:200]}")

    # Verify that stix_objects is a list
    assert isinstance(stix_objects, list), "stix_objects should be a list"
    assert len(stix_objects) > 0, "stix_objects should not be empty"
    
    # Limit the number of objects to check if there are many
    objects_to_check = stix_objects[:5] if len(stix_objects) > 5 else stix_objects
    
    # Verify structure of each STIX object
    for stix_obj in objects_to_check:
        # Verify STIX object is a dictionary
        assert isinstance(stix_obj, dict), "Each STIX object should be a dictionary"
        
        # Verify essential STIX object fields
        assert "type" in stix_obj, "Each STIX object should have a 'type' field"
        assert "id" in stix_obj, "Each STIX object should have an 'id' field"
        assert "spec_version" in stix_obj, "Each STIX object should have a 'spec_version' field"
        
        # Verify STIX ID format (should start with object type and contain UUID)
        stix_id = stix_obj["id"]
        stix_type = stix_obj["type"]
        assert stix_id.startswith(f"{stix_type}--"), f"STIX ID {stix_id} should start with {stix_type}--"
        
        # Check for common STIX object types
        valid_stix_types = [
            "indicator", "malware", "attack-pattern", "intrusion-set", 
            "campaign", "threat-actor", "vulnerability", "course-of-action",
            "tool", "identity", "marking-definition", "bundle"
        ]
        assert stix_type in valid_stix_types, f"STIX type {stix_type} should be a valid STIX object type"
        
        # Check for additional common fields
        common_fields = ["created", "modified", "labels"]
        present_common = [field for field in common_fields if field in stix_obj]
        
        print(f"STIX object {stix_id} of type {stix_type} contains these common fields: {', '.join(present_common)}")
        
        # Log the structure of the first STIX object for debugging
        if stix_obj == objects_to_check[0]:
            print(f"Example STIX object structure: {stix_obj}")

    print(f"Successfully retrieved and validated {len(stix_objects)} STIX objects")

    return True