# 5-test_message_retrieval.py

async def test_message_retrieval(zerg_state=None):
    """Test Slack message retrieval for selected channel"""
    print("Attempting to authenticate using Slack connector")

    assert zerg_state, "this test requires valid zerg_state"

    slack_bot_token = zerg_state.get("slack_bot_token").get("value")
    slack_workspace_url = zerg_state.get("slack_workspace_url").get("value")

    from connectors.slack.config import SlackConnectorConfig
    from connectors.slack.connector import SlackConnector
    from connectors.slack.tools import SlackConnectorTools, GetSlackMessagesInput
    from connectors.slack.target import SlackTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SlackConnectorConfig(
        bot_token=slack_bot_token,
        workspace_url=slack_workspace_url
    )
    assert isinstance(config, ConnectorConfig), "SlackConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SlackConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SlackConnectorConfig should be of type ConnectorConfig"

    # get query target options
    slack_query_target_options = await connector.get_query_target_options()
    assert isinstance(slack_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select channel to target
    channel_selector = None
    for selector in slack_query_target_options.selectors:
        if selector.type == 'channel_ids':  
            channel_selector = selector
            break

    assert channel_selector, "failed to retrieve channel selector from query target options"

    assert isinstance(channel_selector.values, list), "channel_selector values must be a list"
    channel_id = channel_selector.values[0] if channel_selector.values else None
    print(f"Selecting channel id: {channel_id}")

    assert channel_id, f"failed to retrieve channel id from channel selector"

    # set up the target with channel id
    target = SlackTarget(channel_ids=[channel_id])
    assert isinstance(target, ConnectorTargetInterface), "SlackTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_slack_messages tool and execute it with channel id
    get_slack_messages_tool = next(tool for tool in tools if tool.name == "get_slack_messages")
    slack_messages_result = await get_slack_messages_tool.execute(channel_id=channel_id)
    slack_messages = slack_messages_result.result

    print("Type of returned slack_messages:", type(slack_messages))
    print(f"len messages: {len(slack_messages)} messages: {str(slack_messages)[:200]}")

    # Verify that slack_messages is a list
    assert isinstance(slack_messages, list), "slack_messages should be a list"
    assert len(slack_messages) > 0, "slack_messages should not be empty"
    
    # Limit the number of messages to check if there are many
    messages_to_check = slack_messages[:5] if len(slack_messages) > 5 else slack_messages
    
    # Verify structure of each message object
    for message in messages_to_check:
        # Verify essential Slack message fields
        assert "ts" in message, "Each message should have a 'ts' (timestamp) field"
        assert "user" in message or "bot_id" in message, "Each message should have a 'user' or 'bot_id' field"
        assert "text" in message, "Each message should have a 'text' field"
        
        # Verify common Slack message fields
        assert "type" in message, "Each message should have a 'type' field"
        
        # Check for additional optional fields
        optional_fields = ["attachments", "blocks", "thread_ts", "reply_count", "reactions", "edited", "files"]
        present_optional = [field for field in optional_fields if field in message]
        
        print(f"Message {message['ts']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first message for debugging
        if message == messages_to_check[0]:
            print(f"Example message structure: {message}")

    print(f"Successfully retrieved and validated {len(slack_messages)} Slack messages")

    return True