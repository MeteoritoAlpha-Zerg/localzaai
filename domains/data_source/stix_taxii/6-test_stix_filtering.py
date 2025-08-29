# 6-test_stix_filtering.py

async def test_stix_filtering(zerg_state=None):
    """Test STIX object filtering by type and attributes"""
    print("Testing STIX object filtering")

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

    # get query target options to find available collections
    stix_taxii_query_target_options = await connector.get_query_target_options()
    assert isinstance(stix_taxii_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select collection to target for filtering
    collection_selector = None
    for selector in stix_taxii_query_target_options.selectors:
        if selector.type == 'collection_ids':  
            collection_selector = selector
            break

    assert collection_selector, "failed to retrieve collection selector from query target options"

    assert isinstance(collection_selector.values, list), "collection_selector values must be a list"
    collection_id = collection_selector.values[0] if collection_selector.values else None
    print(f"Using collection for filtering: {collection_id}")

    assert collection_id, f"failed to retrieve collection ID from collection selector"

    # set up the target with collection ID
    target = STIXTAXIITarget(collection_ids=[collection_id])
    assert isinstance(target, ConnectorTargetInterface), "STIXTAXIITarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the filter_stix_objects tool and execute it with specific filter criteria
    filter_stix_objects_tool = next(tool for tool in tools if tool.name == "filter_stix_objects")
    
    # Test filtering by STIX object type - filter for indicators
    filter_criteria = {
        "collection_id": collection_id,
        "object_type": "indicator"
    }
    
    filtered_result = await filter_stix_objects_tool.execute(**filter_criteria)
    filtered_objects = filtered_result.result

    print("Type of returned filtered_objects:", type(filtered_objects))
    print(f"len filtered objects: {len(filtered_objects)} objects: {str(filtered_objects)[:200]}")

    # Verify that filtered_objects is a list
    assert isinstance(filtered_objects, list), "filtered_objects should be a list"
    
    # If we have results, verify they match the filter criteria
    if len(filtered_objects) > 0:
        # Limit the number of objects to check if there are many
        objects_to_check = filtered_objects[:3] if len(filtered_objects) > 3 else filtered_objects
        
        # Verify each filtered object matches the criteria
        for stix_obj in objects_to_check:
            # Verify STIX object is a dictionary
            assert isinstance(stix_obj, dict), "Each filtered STIX object should be a dictionary"
            
            # Verify essential STIX object fields
            assert "type" in stix_obj, "Each filtered STIX object should have a 'type' field"
            assert "id" in stix_obj, "Each filtered STIX object should have an 'id' field"
            
            # Verify the object matches the filter criteria
            assert stix_obj["type"] == "indicator", f"Filtered object type {stix_obj['type']} should match filter criteria 'indicator'"
            
            # Verify STIX ID format
            stix_id = stix_obj["id"]
            assert stix_id.startswith("indicator--"), f"Filtered STIX ID {stix_id} should start with 'indicator--'"
            
            # Check for indicator-specific fields
            indicator_fields = ["pattern", "labels", "valid_from"]
            present_indicator_fields = [field for field in indicator_fields if field in stix_obj]
            
            print(f"Filtered indicator {stix_id} contains these indicator fields: {', '.join(present_indicator_fields)}")
            
            # Log the structure of the first filtered object for debugging
            if stix_obj == objects_to_check[0]:
                print(f"Example filtered STIX object structure: {stix_obj}")

        print(f"Successfully filtered and validated {len(filtered_objects)} STIX indicator objects")
    else:
        print("No objects matched the filter criteria - this is acceptable if collection contains no indicators")
    
    # Test another filter - try filtering by a different type if indicators weren't found
    if len(filtered_objects) == 0:
        print("Testing alternative filter for malware objects")
        
        alt_filter_criteria = {
            "collection_id": collection_id,
            "object_type": "malware"
        }
        
        alt_filtered_result = await filter_stix_objects_tool.execute(**alt_filter_criteria)
        alt_filtered_objects = alt_filtered_result.result
        
        assert isinstance(alt_filtered_objects, list), "alt_filtered_objects should be a list"
        
        if len(alt_filtered_objects) > 0:
            # Verify at least one object matches the alternative filter
            sample_obj = alt_filtered_objects[0]
            assert sample_obj["type"] == "malware", f"Alternative filtered object type should be 'malware'"
            print(f"Successfully found {len(alt_filtered_objects)} malware objects with alternative filter")

    return True