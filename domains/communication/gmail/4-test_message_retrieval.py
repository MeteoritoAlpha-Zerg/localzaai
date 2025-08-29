# 4-test_message_retrieval.py

async def test_message_retrieval(zerg_state=None):
    """Test Gmail message retrieval by way of connector tools"""
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
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = GmailConnectorConfig(
        oauth_client_id=gmail_oauth_client_id, oauth_client_secret=gmail_oauth_client_secret,
        oauth_refresh_token=gmail_oauth_refresh_token, api_base_url=gmail_api_base_url, api_version=gmail_api_version
    )

    connector = GmailConnector
    await connector.initialize(config=config, user_id="test_user_id", encryption_key="test_enc_key")

    # Get query target options and select labels
    gmail_query_target_options = await connector.get_query_target_options()
    label_selector = next((s for s in gmail_query_target_options.selectors if s.type == 'label_ids'), None)
    assert label_selector, "failed to retrieve label selector from query target options"

    # Select INBOX and SENT labels (common Gmail labels)
    num_labels = 2
    label_ids = ["INBOX", "SENT"] if "INBOX" in label_selector.values else label_selector.values[:num_labels]
    print(f"Selecting label IDs: {label_ids}")
    assert label_ids, f"failed to retrieve {num_labels} label IDs"

    # Set up target and get tools
    target = GmailTarget(label_ids=label_ids)
    assert isinstance(target, ConnectorTargetInterface), "GmailTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    get_messages_tool = next(tool for tool in tools if tool.name == "get_gmail_messages")
    messages_result = await get_messages_tool.execute(max_results=10)
    gmail_messages = messages_result.result

    print("Type of returned gmail_messages:", type(gmail_messages))
    print(f"len messages: {len(gmail_messages)} messages: {str(gmail_messages)[:200]}")

    # Validate results
    assert isinstance(gmail_messages, list), "gmail_messages should be a list"
    
    # Gmail might have no messages, so we don't assert length > 0
    if len(gmail_messages) > 0:
        for message in gmail_messages[:3]:  # Check first 3 messages
            assert "id" in message, "Each message should have an 'id' field"
            assert "threadId" in message, "Each message should have a 'threadId' field"
            
            # Check for message payload
            if "payload" in message:
                payload = message["payload"]
                assert isinstance(payload, dict), "Payload should be a dictionary"
                
                # Check for headers
                if "headers" in payload:
                    headers = payload["headers"]
                    assert isinstance(headers, list), "Headers should be a list"
                    
                    # Look for common email headers
                    header_names = [h.get("name", "").lower() for h in headers]
                    common_headers = ["from", "to", "subject", "date"]
                    present_headers = [h for h in common_headers if h in header_names]
                    print(f"Message {message['id']} contains headers: {', '.join(present_headers)}")

        print(f"Successfully retrieved and validated {len(gmail_messages)} Gmail messages")
    else:
        print("No messages found in selected labels - validation passed")

    return True