# 5-test_email_retrieval.py

async def test_email_retrieval(zerg_state=None):
    """Test SMTP Email message retrieval for selected folder"""
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
    from connectors.smtp_email.tools import SMTPEmailConnectorTools, GetEmailsInput
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

    # grab the get_emails tool and execute it with folder name
    get_emails_tool = next(tool for tool in tools if tool.name == "get_emails")
    emails_result = await get_emails_tool.execute(folder_name=folder_name)
    emails = emails_result.result

    print("Type of returned emails:", type(emails))
    print(f"len emails: {len(emails)} emails: {str(emails)[:200]}")

    # Verify that emails is a list
    assert isinstance(emails, list), "emails should be a list"
    assert len(emails) > 0, "emails should not be empty"
    
    # Limit the number of emails to check if there are many
    emails_to_check = emails[:5] if len(emails) > 5 else emails
    
    # Verify structure of each email object
    for email in emails_to_check:
        # Verify essential email fields
        assert "uid" in email, "Each email should have a 'uid' field"
        assert "subject" in email, "Each email should have a 'subject' field"
        assert "from" in email, "Each email should have a 'from' field"
        assert "date" in email, "Each email should have a 'date' field"
        
        # Verify common email fields
        assert "to" in email, "Each email should have a 'to' field"
        assert "message_id" in email, "Each email should have a 'message_id' field"
        
        # Check for additional optional fields
        optional_fields = ["cc", "bcc", "reply_to", "body_text", "body_html", "attachments", "flags", "size"]
        present_optional = [field for field in optional_fields if field in email]
        
        print(f"Email {email['uid']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first email for debugging
        if email == emails_to_check[0]:
            print(f"Example email structure: {email}")

    print(f"Successfully retrieved and validated {len(emails)} emails")

    return True