# 7-test_email_content.py

async def test_email_content(zerg_state=None):
    """Test SMTP Email content retrieval including attachments"""
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
    from connectors.smtp_email.tools import SMTPEmailConnectorTools, GetEmailContentInput
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

    # select folder to target
    folder_selector = None
    for selector in smtp_email_query_target_options.selectors:
        if selector.type == 'folder_names':  
            folder_selector = selector
            break

    assert folder_selector, "failed to retrieve folder selector from query target options"

    assert isinstance(folder_selector.values, list), "folder_selector values must be a list"
    folder_name = folder_selector.values[0] if folder_selector.values else None
    print(f"Selecting folder name: {folder_name}")

    assert folder_name, f"failed to retrieve folder name from folder selector"

    # set up the target with folder name
    target = SMTPEmailTarget(folder_names=[folder_name])
    assert isinstance(target, ConnectorTargetInterface), "SMTPEmailTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # First get a list of emails to find one to retrieve content for
    get_emails_tool = next(tool for tool in tools if tool.name == "get_emails")
    emails_result = await get_emails_tool.execute(folder_name=folder_name)
    emails = emails_result.result

    assert isinstance(emails, list), "emails should be a list"
    assert len(emails) > 0, "emails should not be empty"

    # Use the first email for content retrieval test
    test_email = emails[0]
    email_uid = test_email["uid"]
    print(f"Testing content retrieval for email UID: {email_uid}")

    # grab the get_email_content tool and execute it with email UID
    get_email_content_tool = next(tool for tool in tools if tool.name == "get_email_content")
    email_content_result = await get_email_content_tool.execute(
        folder_name=folder_name,
        email_uid=email_uid
    )
    email_content = email_content_result.result

    print("Type of returned email_content:", type(email_content))
    print(f"Email content keys: {list(email_content.keys()) if isinstance(email_content, dict) else 'Not a dict'}")

    # Verify that email_content is a dictionary
    assert isinstance(email_content, dict), "email_content should be a dict"
    
    # Verify essential email content fields
    assert "uid" in email_content, "Email content should have a 'uid' field"
    assert email_content["uid"] == email_uid, "Email content UID should match requested UID"
    
    assert "headers" in email_content, "Email content should have a 'headers' field"
    assert isinstance(email_content["headers"], dict), "headers should be a dict"
    
    # Verify essential headers
    headers = email_content["headers"]
    essential_headers = ["subject", "from", "to", "date", "message-id"]
    for header in essential_headers:
        assert header in headers, f"Headers should contain '{header}'"
    
    # Verify body content
    assert "body" in email_content, "Email content should have a 'body' field"
    body = email_content["body"]
    
    # Check for text and/or HTML content
    content_types = ["text", "html"]
    present_content = [content_type for content_type in content_types if content_type in body]
    assert len(present_content) > 0, "Email should have at least text or html content"
    
    print(f"Email body contains these content types: {', '.join(present_content)}")
    
    # Check for attachments (optional)
    if "attachments" in email_content:
        attachments = email_content["attachments"]
        assert isinstance(attachments, list), "attachments should be a list"
        
        if len(attachments) > 0:
            # Verify attachment structure
            for attachment in attachments:
                assert "filename" in attachment, "Each attachment should have a 'filename'"
                assert "content_type" in attachment, "Each attachment should have a 'content_type'"
                assert "size" in attachment, "Each attachment should have a 'size'"
                
            print(f"Email has {len(attachments)} attachments")
        else:
            print("Email has no attachments")
    
    # Check for additional optional fields
    optional_fields = ["raw_message", "mime_structure", "flags"]
    present_optional = [field for field in optional_fields if field in email_content]
    
    print(f"Email content contains these optional fields: {', '.join(present_optional)}")
    
    # Log a summary of the email content structure
    print(f"Example email content structure summary:")
    print(f"  - UID: {email_content['uid']}")
    print(f"  - Subject: {headers.get('subject', 'N/A')}")
    print(f"  - From: {headers.get('from', 'N/A')}")
    print(f"  - Body types: {', '.join(present_content)}")
    if "attachments" in email_content:
        print(f"  - Attachments: {len(email_content['attachments'])}")

    print(f"Successfully retrieved and validated email content for UID {email_uid}")

    return True