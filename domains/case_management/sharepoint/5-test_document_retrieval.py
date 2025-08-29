# 5-test_document_retrieval.py

async def test_document_retrieval(zerg_state=None):
    """Test SharePoint document retrieval"""

    print("Attempting to retrieve documents using SharePoint connector")

    assert zerg_state, "this test requires valid zerg_state"

    sharepoint_url = zerg_state.get("sharepoint_url").get("value")
    sharepoint_client_id = zerg_state.get("sharepoint_client_id").get("value")
    sharepoint_client_secret = zerg_state.get("sharepoint_client_secret").get("value")
    sharepoint_tenant_id = zerg_state.get("sharepoint_tenant_id").get("value")

    from connectors.sharepoint.config import SharePointConnectorConfig
    from connectors.sharepoint.connector import SharePointConnector
    from connectors.sharepoint.tools import SharePointConnectorTools
    from connectors.sharepoint.target import SharePointTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SharePointConnectorConfig(
        url=sharepoint_url,
        client_id=sharepoint_client_id,
        client_secret=sharepoint_client_secret,
        tenant_id=sharepoint_tenant_id
    )
    assert isinstance(config, ConnectorConfig), "SharePointConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SharePointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SharePointConnector should be of type Connector"

    # get query target options
    sharepoint_query_target_options = await connector.get_query_target_options()
    assert isinstance(sharepoint_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select sites to target
    site_selector = None
    for selector in sharepoint_query_target_options.selectors:
        if selector.type == 'site':  
            site_selector = selector
            break

    assert site_selector, "failed to retrieve site selector from query target options"

    # grab the first site
    assert isinstance(site_selector.values, list), "site_selector values must be a list"
    site_name = site_selector.values[0] if site_selector.values else None
    print(f"Selecting site name: {site_name}")

    assert site_name, "failed to retrieve site name from site selector"

    # Create target with the site name
    target = SharePointTarget(site_names=[site_name])
    assert isinstance(target, ConnectorTargetInterface), "SharePointTarget should be of type ConnectorTargetInterface"

    # Get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # First get document libraries
    libraries_tool = next(tool for tool in tools if tool.name == "get_sharepoint_document_libraries")
    libraries_result = await libraries_tool.execute()
    libraries = libraries_result.result

    assert isinstance(libraries, list), "SharePoint libraries should be a list"
    assert len(libraries) > 0, "No SharePoint document libraries found"
    
    # Select the first library
    first_library = libraries[0]
    library_name = first_library.get('name')
    print(f"Selected library: {library_name}")
    
    # Update target to include the library
    target = SharePointTarget(site_names=[site_name], library_names=[library_name])
    
    # Get updated tools with the new target
    tools = await connector.get_tools(
        target=target
    )
    
    # Get the document retrieval tool
    documents_tool = next(tool for tool in tools if tool.name == "get_sharepoint_documents")
    documents_result = await documents_tool.execute()
    documents = documents_result.result
    
    print("Type of returned documents:", type(documents))
    print(f"Retrieved {len(documents)} documents from library {library_name}")
    print(f"Documents preview: {str(documents)[:200]}")
    
    # Validate documents
    assert isinstance(documents, list), "SharePoint documents should be a list"
    
    if len(documents) > 0:
        # Verify structure of each document
        for document in documents:
            assert "id" in document, "Each document should have an 'id' field"
            assert "name" in document, "Each document should have a 'name' field"
            
            # Common SharePoint document fields
            expected_fields = ["webUrl", "size", "lastModifiedDateTime", "file"]
            present_fields = [field for field in expected_fields if field in document]
            
            # Log document metadata
            print(f"Document '{document['name']}' contains these fields: {', '.join(present_fields)}")
            
            # Check file metadata if available
            if "file" in document and isinstance(document["file"], dict):
                file_info = document["file"]
                if "mimeType" in file_info:
                    print(f"Document '{document['name']}' has MIME type: {file_info['mimeType']}")
            
            # Log the full structure of the first document only
            if document == documents[0]:
                print(f"Example document structure: {document}")
        
        print(f"Successfully retrieved and validated {len(documents)} SharePoint documents")
    else:
        print(f"No documents found in library {library_name}")
    
    return True