# 4-test_list_collections.py

async def test_list_collections(zerg_state=None):
    """Test TAXII collection enumeration by way of connector tools"""
    print("Testing TAXII collection listing")

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

    # select collections to target
    collection_selector = None
    for selector in stix_taxii_query_target_options.selectors:
        if selector.type == 'collection_ids':  
            collection_selector = selector
            break

    assert collection_selector, "failed to retrieve collection selector from query target options"

    # grab the first two collections 
    num_collections = 2
    assert isinstance(collection_selector.values, list), "collection_selector values must be a list"
    collection_ids = collection_selector.values[:num_collections] if collection_selector.values else None
    print(f"Selecting collection IDs: {collection_ids}")

    assert collection_ids, f"failed to retrieve {num_collections} collection IDs from collection selector"

    # set up the target with collection IDs
    target = STIXTAXIITarget(collection_ids=collection_ids)
    assert isinstance(target, ConnectorTargetInterface), "STIXTAXIITarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_taxii_collections tool
    taxii_get_collections_tool = next(tool for tool in tools if tool.name == "get_taxii_collections")
    taxii_collections_result = await taxii_get_collections_tool.execute()
    taxii_collections = taxii_collections_result.result

    print("Type of returned taxii_collections:", type(taxii_collections))
    print(f"len collections: {len(taxii_collections)} collections: {str(taxii_collections)[:200]}")

    # Verify that taxii_collections is a list
    assert isinstance(taxii_collections, list), "taxii_collections should be a list"
    assert len(taxii_collections) > 0, "taxii_collections should not be empty"
    assert len(taxii_collections) == num_collections, f"taxii_collections should have {num_collections} entries"
    
    # Verify structure of each collection object
    for collection in taxii_collections:
        assert "id" in collection, "Each collection should have an 'id' field"
        assert collection["id"] in collection_ids, f"Collection ID {collection['id']} is not in the requested collection_ids"
        
        # Verify essential TAXII collection fields
        assert "title" in collection, "Each collection should have a 'title' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["description", "can_read", "can_write", "media_types"]
        present_fields = [field for field in descriptive_fields if field in collection]
        
        print(f"Collection {collection['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Verify media_types contains STIX content if present
        if "media_types" in collection:
            media_types = collection["media_types"]
            assert isinstance(media_types, list), "media_types should be a list"
            
        # Log the full structure of the first collection
        if collection == taxii_collections[0]:
            print(f"Example collection structure: {collection}")

    print(f"Successfully retrieved and validated {len(taxii_collections)} TAXII collections")

    return True