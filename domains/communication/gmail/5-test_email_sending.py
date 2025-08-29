# 5-test_email_sending.py

async def test_email_sending(zerg_state=None):
    """Test Gmail email sending by way of connector tools"""
    print("Attempting to authenticate using Gmail connector")

    assert zerg_state, "this test requires valid zerg_state"

    # Config setup
    gmail_oauth_client_id = zerg_state.get("gmail_oauth_client_id").get("value")
    gmail_oauth_client_secret = zerg_state.get("gmail_oauth_client_secret").get("value")
    gmail_oauth_refresh_token = zerg_state.get("gmail_oauth_refresh_token").get("value")
    gmail_api_base_url = zerg_state.get("gmail_api_base_url").get("value")
    gmail_api_version = zerg_state.get("gmail_api_version").get("value")

    from connectors.gmail.config import GmailConnectorConfig
    from connectors.gmail.connector import GmailConnector
    from connectors.gmail.target import GmailTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    config = GmailConnectorConfig(
        oauth_client_id=gmail_oauth_client_id, oauth_client_secret=gmail_oauth_client_secret,
        oauth_refresh_token=gmail_oauth_refresh_token, api_base_url=gmail_api_base_url, api_version=gmail_api_version
    )

    connector = GmailConnector
    await connector.initialize(config=config, user_id="test_user_id", encryption_key="test_enc_key")

    # Set up target for sending (no specific labels needed)
    target = GmailTarget()
    tools = await connector.get_tools(target=target)
    send_email_tool = next(tool for tool in tools if tool.name == "send_gmail_message")
    
    # Send a test email (to self to avoid external sends)
    import time
    timestamp = int(time.time())
    
    send_result = await send_email_tool.execute(
        to="test@example.com",  # Use test email or get from profile
        subject=f"Test Email from Gmail Connector - {timestamp}",
        body="This is a test email sent through the Gmail connector for validation purposes.",
        body_type="text"
    )
    send_response = send_result.result

    print("Type of returned send_response:", type(send_response))
    print(f"Email send response: {str(send_response)[:200]}")

    # Validate send response
    assert isinstance(send_response, dict), "send_response should be a dictionary"
    assert len(send_response) > 0, "send_response should not be empty"
    
    # Check for essential Gmail send response fields
    assert "id" in send_response, "Send response should have an 'id' field"
    assert "threadId" in send_response, "Send response should have a 'threadId' field"
    
    # Check for label IDs (sent emails typically get SENT label)
    if "labelIds" in send_response:
        label_ids = send_response["labelIds"]
        assert isinstance(label_ids, list), "Label IDs should be a list"
        print(f"Sent email assigned to labels: {label_ids}")
    
    message_id = send_response["id"]
    print(f"Successfully sent email with ID: {message_id}")

    # Optional: Verify the email was actually sent by trying to retrieve it
    # This would require additional API calls and may not be necessary for basic validation
    
    print("Successfully validated Gmail email sending functionality")
    return True