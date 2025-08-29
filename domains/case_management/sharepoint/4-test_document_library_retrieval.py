# 4-test_document_library_retrieval.py

async def test_document_library_retrieval(zerg_state=None):
    """Test SharePoint document library retrieval by way of query target options"""

    print("Attempting to authenticate using SharePoint connector")

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

    # grab the first site for now
    #num_sites = 1
    assert isinstance(site_selector.values, list), "site_selector values must be a list"
    site_name = site_selector.values[0] if site_selector.values else None
    print(f"Selecting site name: {site_name}")

    assert site_name, "failed to retrieve site name from site selector"

    # set up the target with site name
    target = SharePointTarget(site_names=[site_name])
    assert isinstance(target, ConnectorTargetInterface), "SharePointTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_sharepoint_document_libraries tool
    sharepoint_get_libraries_tool = next(tool for tool in tools if tool.name == "get_sharepoint_document_libraries")
    sharepoint_libraries_result = await sharepoint_get_libraries_tool.execute()
    sharepoint_libraries = sharepoint_libraries_result.result
    
    print("Type of returned sharepoint_libraries:", type(sharepoint_libraries))
    print(f"len libraries: {len(sharepoint_libraries)} libraries: {str(sharepoint_libraries)[:200]}")

    # Verify that sharepoint_libraries is a list
    assert isinstance(sharepoint_libraries, list), "sharepoint_libraries should be a list"
    assert len(sharepoint_libraries) > 0, "sharepoint_libraries should not be empty"
    
    # Verify structure of each document library object
    for library in sharepoint_libraries:
        assert "id" in library, "Each document library should have an 'id' field"
        assert "name" in library, "Each document library should have a 'name' field"
        assert "serverRelativeUrl" in library, "Each document library should have a 'serverRelativeUrl' field"
        
        # Verify the document library belongs to the selected site
        assert "siteUrl" in library, "Each document library should have a 'siteUrl' field"
        
        # Check for additional descriptive fields (common in SharePoint document libraries)
        descriptive_fields = ["description", "createdDateTime", "lastModifiedDateTime", "webUrl", "driveId"]
        present_fields = [field for field in descriptive_fields if field in library]
        
        print(f"Library {library['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first library
        if library == sharepoint_libraries[0]:
            print(f"Example document library structure: {library}")

    print(f"Successfully retrieved and validated {len(sharepoint_libraries)} SharePoint document libraries")

    return True