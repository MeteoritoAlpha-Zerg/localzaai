# 6-test_send_email.py

from datetime import datetime

async def test_send_email(zerg_state=None):
    """Test SMTP Email sending via SMTP server"""
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
    from connectors.smtp_email.tools import SMTPEmailConnectorTools, SendEmailInput
    from connectors.smtp_email.target import SMTPEmailTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

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

    # set up the target (no specific targeting needed for sending)
    target = SMTPEmailTarget()
    assert isinstance(target, ConnectorTargetInterface), "SMTPEmailTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the send_email tool and execute it with test email
    send_email_tool = next(tool for tool in tools if tool.name == "send_email")
    test_subject = f"Test email from SMTP connector at {datetime.now().isoformat()}"
    test_body = f"This is a test email sent via the SMTP Email connector at {datetime.now().isoformat()}"
    test_recipient = email_username  # Send to self for testing
    
    send_result = await send_email_tool.execute(
        to=test_recipient,
        subject=test_subject,
        body=test_body
    )
    send_response = send_result.result

    print("Type of returned send_response:", type(send_response))
    print(f"Send response: {send_response}")

    # Verify that the email was sent successfully
    assert isinstance(send_response, dict), "send_response should be a dict"
    
    # Verify essential response fields
    assert "success" in send_response, "Response should have a 'success' field"
    assert send_response["success"] is True, "Email send should be successful"
    
    # Check for additional response fields that indicate successful delivery
    expected_fields = ["message_id", "timestamp", "recipient"]
    for field in expected_fields:
        if field in send_response:
            print(f"Response contains field '{field}': {send_response[field]}")
            
            # Verify recipient matches if present
            if field == "recipient":
                assert send_response[field] == test_recipient, f"Response recipient should match requested recipient"
    
    # Verify at least one of the expected fields is present (indicating proper SMTP response)
    present_fields = [field for field in expected_fields if field in send_response]
    assert len(present_fields) > 0, "Response should contain at least one of: message_id, timestamp, or recipient"

    print(f"Successfully sent email to {test_recipient}")
    print(f"Response structure: {send_response}")

    return True