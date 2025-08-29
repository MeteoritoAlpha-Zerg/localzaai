# 4-test_list_indices.py

async def test_list_indices(zerg_state=None):
    """Test Elasticsearch index enumeration by way of connector tools"""
    print("Attempting to authenticate using Elastic connector")

    assert zerg_state, "this test requires valid zerg_state"

    elastic_url = zerg_state.get("elastic_url").get("value")
    elastic_api_key = zerg_state.get("elastic_api_key").get("value")
    elastic_username = zerg_state.get("elastic_username", {}).get("value")
    elastic_password = zerg_state.get("elastic_password", {}).get("value")

    from connectors.elastic.config import ElasticConnectorConfig
    from connectors.elastic.connector import ElasticConnector
    from connectors.elastic.tools import ElasticConnectorTools
    from connectors.elastic.target import ElasticTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config - prefer API key over username/password
    if elastic_api_key:
        config = ElasticConnectorConfig(
            url=elastic_url,
            api_key=elastic_api_key,
        )
    elif elastic_username and elastic_password:
        config = ElasticConnectorConfig(
            url=elastic_url,
            username=elastic_username,
            password=elastic_password,
        )
    else:
        raise Exception("Either elastic_api_key or both elastic_username and elastic_password must be provided")

    assert isinstance(config, ConnectorConfig), "ElasticConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ElasticConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ElasticConnector should be of type Connector"

    # get query target options
    elastic_query_target_options = await connector.get_query_target_options()
    assert isinstance(elastic_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select indices to target
    index_selector = None
    for selector in elastic_query_target_options.selectors:
        if selector.type == 'index_names':  
            index_selector = selector
            break

    assert index_selector, "failed to retrieve index selector from query target options"

    # grab the first two indices 
    num_indices = 2
    assert isinstance(index_selector.values, list), "index_selector values must be a list"
    index_names = index_selector.values[:num_indices] if index_selector.values else None
    print(f"Selecting index names: {index_names}")

    assert index_names, f"failed to retrieve {num_indices} index names from index selector"

    # set up the target with index names
    target = ElasticTarget(index_names=index_names)
    assert isinstance(target, ConnectorTargetInterface), "ElasticTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_elastic_indices tool
    elastic_get_indices_tool = next(tool for tool in tools if tool.name == "get_elastic_indices")
    elastic_indices_result = await elastic_get_indices_tool.execute()
    elastic_indices = elastic_indices_result.result

    print("Type of returned elastic_indices:", type(elastic_indices))
    print(f"len indices: {len(elastic_indices)} indices: {str(elastic_indices)[:200]}")

    # Verify that elastic_indices is a list
    assert isinstance(elastic_indices, list), "elastic_indices should be a list"
    assert len(elastic_indices) > 0, "elastic_indices should not be empty"
    assert len(elastic_indices) == num_indices, f"elastic_indices should have {num_indices} entries"
    
    # Verify structure of each index object
    for index in elastic_indices:
        assert "index" in index, "Each index should have an 'index' field"
        assert index["index"] in index_names, f"Index name {index['index']} is not in the requested index_names"
        
        # Verify essential Elasticsearch index fields
        assert "health" in index, "Each index should have a 'health' field"
        assert "status" in index, "Each index should have a 'status' field"
        assert "docs.count" in index, "Each index should have a 'docs.count' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["uuid", "pri", "rep", "store.size", "pri.store.size"]
        present_fields = [field for field in descriptive_fields if field in index]
        
        print(f"Index {index['index']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first index
        if index == elastic_indices[0]:
            print(f"Example index structure: {index}")

    print(f"Successfully retrieved and validated {len(elastic_indices)} Elasticsearch indices")

    return True