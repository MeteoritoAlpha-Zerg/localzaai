async def test_sensitive_content_scan(zerg_state=None):
    """Test SharePoint sensitive content scanning"""

    from pydantic import SecretStr

    print("Scanning for sensitive content using SharePoint connector")

    assert zerg_state, "this test requires valid zerg_state"

    sharepoint_url = zerg_state.get("sharepoint_url").get("value")
    sharepoint_client_id = zerg_state.get("sharepoint_client_id").get("value")
    sharepoint_client_secret = zerg_state.get("sharepoint_client_secret").get("value")
    sharepoint_tenant_id = zerg_state.get("sharepoint_tenant_id").get("value")

    from connectors.sharepoint.config import SharePointConnectorConfig
    from connectors.sharepoint.connector import SharePointConnector
    from connectors.sharepoint.tools import SharePointConnectorTools
    from connectors.sharepoint.target import SharePointTarget

    config = SharePointConnectorConfig(
        url=sharepoint_url,
        client_id=sharepoint_client_id,
        client_secret=sharepoint_client_secret,
        tenant_id=sharepoint_tenant_id
    )
    connector = SharePointConnector(config)

    connector_target = SharePointTarget(config=config)
    
    # Get connector tools
    tools = SharePointConnectorTools(
        sharepoint_config=config, 
        target=SharePointTarget, 
        connector_display_name="SharePoint"
    )
    
    # Get sensitive content patterns from config
    sensitive_patterns = zerg_state.get("sensitive_content_patterns").get("value")
    
    # Get a list of sites to scan (limit to configured max for test)
    sites_to_scan = await tools.get_sharepoint_sites(
        limit=zerg_state.get("max_sites_to_scan").get("value")
    )
    
    total_documents = 0
    sensitive_documents = []
    
    # Scan each site
    for site in sites_to_scan:
        site_name = site.get('name')
        print(f"Scanning site: {site_name}")
        
        # Set site in target
        connector_target.site_name = site_name
        
        # Get document libraries
        libraries = await tools.get_sharepoint_document_libraries()
        
        # Scan each library
        for library in libraries:
            library_name = library.get('name')
            
            # Set library in target
            connector_target.library_name = library_name
            
            try:
                # Get documents in this library
                documents = await tools.get_sharepoint_documents()
                total_documents += len(documents)
                
                # Scan each document (simulated in test, would download and scan in real implementation)
                for document in documents:
                    # For test purposes, just check if document name/metadata matches sensitive patterns
                    # In real implementation, would extract and scan content
                    for pattern in sensitive_patterns:
                        doc_name = document.get('name', '').lower()
                        if pattern.lower() in doc_name:
                            document['matched_pattern'] = pattern
                            document['site_name'] = site_name
                            document['library_name'] = library_name
                            sensitive_documents.append(document)
                            break
            
            except Exception as e:
                print(f"Error scanning library {library_name}: {e}")
                continue
    
    print(f"Scanned {total_documents} documents across {len(sites_to_scan)} sites")
    print(f"Found {len(sensitive_documents)} documents with potential sensitive content")
    
    if sensitive_documents:
        for doc in sensitive_documents[:3]:  # Show up to 3 examples
            print(f"Sensitive document: {doc.get('name')} in {doc.get('site_name')}/{doc.get('library_name')}")
            print(f"  Matched pattern: {doc.get('matched_pattern')}")
    
    return True