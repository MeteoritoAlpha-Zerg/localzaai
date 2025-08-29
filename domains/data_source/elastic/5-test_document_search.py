# 5-test_document_search.py

async def test_document_search(zerg_state=None):
    """Test Elasticsearch document search and retrieval"""
    print("Attempting to search documents using Elastic connector")

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

    assert isinstance(index_selector.values, list), "index_selector values must be a list"
    index_name = index_selector.values[0] if index_selector.values else None
    print(f"Selecting index name: {index_name}")

    assert index_name, f"failed to retrieve index name from index selector"

    # set up the target with index names
    target = ElasticTarget(index_names=[index_name])
    assert isinstance(target, ConnectorTargetInterface), "ElasticTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the search_elastic_documents tool and execute it with index name
    search_elastic_documents_tool = next(tool for tool in tools if tool.name == "search_elastic_documents")
    elastic_documents_result = await search_elastic_documents_tool.execute(
        index_name=index_name,
        query="*",  # match all documents
        size=10     # limit to 10 documents
    )
    elastic_documents = elastic_documents_result.result

    print("Type of returned elastic_documents:", type(elastic_documents))
    print(f"len documents: {len(elastic_documents)} documents: {str(elastic_documents)[:200]}")

    # Verify that elastic_documents is a list
    assert isinstance(elastic_documents, list), "elastic_documents should be a list"
    assert len(elastic_documents) > 0, "elastic_documents should not be empty"
    
    # Limit the number of documents to check if there are many
    documents_to_check = elastic_documents[:5] if len(elastic_documents) > 5 else elastic_documents
    
    # Verify structure of each document object
    for document in documents_to_check:
        # Verify essential Elasticsearch document fields
        assert "_index" in document, "Each document should have an '_index' field"
        assert "_id" in document, "Each document should have an '_id' field"
        assert "_source" in document, "Each document should have a '_source' field"
        
        # Check if document belongs to the requested index
        assert document["_index"] == index_name, f"Document {document['_id']} does not belong to the requested index {index_name}"
        
        # Verify common Elasticsearch document fields
        assert "_score" in document, "Each document should have a '_score' field"
        
        # Check for _source object which contains the actual document data
        source = document["_source"]
        assert isinstance(source, dict), "Document _source should be a dictionary"
        
        # Check for timestamp field (common in log data)
        timestamp_fields = ["@timestamp", "timestamp", "time", "date"]
        has_timestamp = any(field in source for field in timestamp_fields)
        
        # Log presence of timestamp field
        timestamp_field = next((field for field in timestamp_fields if field in source), None)
        if timestamp_field:
            print(f"Document {document['_id']} has timestamp field: {timestamp_field}")
        
        # Log the structure of the first document for debugging
        if document == documents_to_check[0]:
            print(f"Example document structure: {document}")

    print(f"Successfully retrieved and validated {len(elastic_documents)} Elasticsearch documents")

    return True