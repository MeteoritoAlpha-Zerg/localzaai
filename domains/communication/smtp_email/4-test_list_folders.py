# 4-test_list_folders.py

async def test_list_folders(zerg_state=None):
    """Test SMTP Email folder enumeration by way of query target options"""
    print("Attempting to authenticate using SMTP Email connector")

    assert zerg_state, "this test requires valid zerg_state"

    smtp_server = zerg_state.get("smtp_server").get("value")
    smtp_port = zerg_state.get("smtp_port").get("value")
    imap_server = zerg_state.get("imap_server").get("value")
    imap_port = zerg_state.get("imap_port").get("value")
    email_username = zerg_state.get("email_username").get("value")
    email_password = zerg_state.get("email_password").get("value")

    from connectors.smtp_email.config import SMTPEmailConnectorConfig
    from connectors.smtp_email.connector import SMTPEmailConnector
    from connectors.smtp_email.tools import SMTPEmailConnectorTools
    from connectors.smtp_email.target import SMTPEmailTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = SMTPEmailConnectorConfig(
        smtp_server=smtp_server,
        smtp_port=int(smtp_port),
        imap_server=imap_server,
        imap_port=int(imap_port),
        username=email_username,
        password=email_password
    )
    assert isinstance(config, ConnectorConfig), "SMTPEmailConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SMTPEmailConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SMTPEmailConnectorConfig should be of type ConnectorConfig"

    # get query target options
    smtp_email_query_target_options = await connector.get_query_target_options()
    assert isinstance(smtp_email_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select folders to target
    folder_selector = None
    for selector in smtp_email_query_target_options.selectors:
        if selector.type == 'folder_names':  
            folder_selector = selector
            break

    assert folder_selector, "failed to retrieve folder selector from query target options"

    # grab the first two folders 
    num_folders = 2
    assert isinstance(folder_selector.values, list), "folder_selector values must be a list"
    folder_names = folder_selector.values[:num_folders] if folder_selector.values else None
    print(f"Selecting folder names: {folder_names}")

    assert folder_names, f"failed to retrieve {num_folders} folder names from folder selector"

    # set up the target with folder names
    target = SMTPEmailTarget(folder_names=folder_names)
    assert isinstance(target, ConnectorTargetInterface), "SMTPEmailTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_email_folders tool
    email_get_folders_tool = next(tool for tool in tools if tool.name == "get_email_folders")
    email_folders_result = await email_get_folders_tool.execute()
    email_folders = email_folders_result.result

    print("Type of returned email_folders:", type(email_folders))
    print(f"len folders: {len(email_folders)} folders: {str(email_folders)[:200]}")

    # ensure that email_folders are a list of objects with the name being the folder name
    # and the object having the folder message count and other relevant information from the email specification
    # as may be descriptive
    # Verify that email_folders is a list
    assert isinstance(email_folders, list), "email_folders should be a list"
    assert len(email_folders) > 0, "email_folders should not be empty"
    assert len(email_folders) == num_folders, f"email_folders should have {num_folders} entries"
    
    # Verify structure of each folder object
    for folder in email_folders:
        assert "name" in folder, "Each folder should have a 'name' field"
        assert folder["name"] in folder_names, f"Folder name {folder['name']} is not in the requested folder_names"
        
        # Verify essential email folder fields
        # These are common fields in email folders based on IMAP specification
        assert "message_count" in folder, "Each folder should have a 'message_count' field"
        assert isinstance(folder["message_count"], int), "message_count should be an integer"
        
        # Check for additional descriptive fields (optional in some email servers)
        descriptive_fields = ["recent_count", "unseen_count", "uidnext", "uidvalidity", "flags"]
        present_fields = [field for field in descriptive_fields if field in folder]
        
        print(f"Folder {folder['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if folder == email_folders[0]:
            print(f"Example folder structure: {folder}")

    print(f"Successfully retrieved and validated {len(email_folders)} email folders")

    return True