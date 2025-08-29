# 4-test_list_indexes.py

async def test_list_indexes(zerg_state=None):
    """Test Splunk index enumeration by way of connector tools"""
    print("Testing Splunk index listing")

    assert zerg_state, "this test requires valid zerg_state"

    splunk_host = zerg_state.get("splunk_host").get("value")
    splunk_port = zerg_state.get("splunk_port").get("value")
    splunk_username = zerg_state.get("splunk_username").get("value")
    splunk_password = zerg_state.get("splunk_password").get("value")
    splunk_hec_token = zerg_state.get("splunk_hec_token").get("value")

    from connectors.splunk.config import SplunkConnectorConfig
    from connectors.splunk.connector import SplunkConnector
    from connectors.splunk.target import SplunkTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = SplunkConnectorConfig(
        host=splunk_host,
        port=int(splunk_port),
        username=splunk_username,
        password=splunk_password,
        hec_token=splunk_hec_token
    )
    assert isinstance(config, ConnectorConfig), "SplunkConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SplunkConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SplunkConnector should be of type Connector"

    # get query target options
    splunk_query_target_options = await connector.get_query_target_options()
    assert isinstance(splunk_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select indexes to target
    index_selector = None
    for selector in splunk_query_target_options.selectors:
        if selector.type == 'index_names':  
            index_selector = selector
            break

    assert index_selector, "failed to retrieve index selector from query target options"

    # grab the first two indexes 
    num_indexes = 2
    assert isinstance(index_selector.values, list), "index_selector values must be a list"
    index_names = index_selector.values[:num_indexes] if index_selector.values else None
    print(f"Selecting index names: {index_names}")

    assert index_names, f"failed to retrieve {num_indexes} index names from index selector"

    # set up the target with index names
    target = SplunkTarget(index_names=index_names)
    assert isinstance(target, ConnectorTargetInterface), "SplunkTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_splunk_indexes tool
    splunk_get_indexes_tool = next(tool for tool in tools if tool.name == "get_splunk_indexes")
    splunk_indexes_result = await splunk_get_indexes_tool.execute()
    splunk_indexes = splunk_indexes_result.result

    print("Type of returned splunk_indexes:", type(splunk_indexes))
    print(f"len indexes: {len(splunk_indexes)} indexes: {str(splunk_indexes)[:200]}")

    # Verify that splunk_indexes is a list
    assert isinstance(splunk_indexes, list), "splunk_indexes should be a list"
    assert len(splunk_indexes) > 0, "splunk_indexes should not be empty"
    assert len(splunk_indexes) == num_indexes, f"splunk_indexes should have {num_indexes} entries"
    
    # Verify structure of each index object
    for index in splunk_indexes:
        assert "name" in index, "Each index should have a 'name' field"
        assert index["name"] in index_names, f"Index name {index['name']} is not in the requested index_names"
        
        # Verify essential Splunk index fields
        assert "currentDBSizeMB" in index or "totalEventCount" in index or "datatype" in index, "Each index should have size or count information"
        
        # Check for additional descriptive fields
        descriptive_fields = ["datatype", "maxSize", "currentDBSizeMB", "totalEventCount", "maxDataSize", "homePath", "coldPath"]
        present_fields = [field for field in descriptive_fields if field in index]
        
        print(f"Index {index['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Verify numeric fields are actually numeric if present
        numeric_fields = ["currentDBSizeMB", "totalEventCount", "maxDataSize"]
        for field in numeric_fields:
            if field in index and index[field] is not None:
                # Handle both string and numeric values
                if isinstance(index[field], str):
                    assert index[field].replace('.', '').replace('-', '').isdigit() or index[field] == "auto", f"Field {field} should be numeric or 'auto'"
                else:
                    assert isinstance(index[field], (int, float)), f"Field {field} should be numeric"
        
        # Verify datatype is valid if present
        if "datatype" in index:
            valid_datatypes = ["event", "metric"]
            assert index["datatype"] in valid_datatypes, f"Datatype should be valid"
        
        # Check for path information if present
        path_fields = ["homePath", "coldPath", "thawedPath"]
        for field in path_fields:
            if field in index and index[field]:
                assert isinstance(index[field], str), f"Path field {field} should be a string"
        
        # Log the full structure of the first index
        if index == splunk_indexes[0]:
            print(f"Example index structure: {index}")

    print(f"Successfully retrieved and validated {len(splunk_indexes)} Splunk indexes")

    return True