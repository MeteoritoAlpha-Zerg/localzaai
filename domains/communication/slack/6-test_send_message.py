# 6-test_send_message.py

from datetime import datetime

async def test_send_message(zerg_state=None):
    """Test Slack message sending to selected channel"""
    print("Attempting to authenticate using Slack connector")

    assert zerg_state, "this test requires valid zerg_state"

    slack_bot_token = zerg_state.get("slack_bot_token").get("value")
    slack_workspace_url = zerg_state.get("slack_workspace_url").get("value")

    from connectors.slack.config import SlackConnectorConfig
    from connectors.slack.connector import SlackConnector
    from connectors.slack.tools import SlackConnectorTools, SendSlackMessageInput
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

    # grab the send_slack_message tool and execute it with channel id and test message
    send_slack_message_tool = next(tool for tool in tools if tool.name == "send_slack_message")
    test_message = f"Test message from Slack connector at {datetime.now().isoformat()}"
    
    send_result = await send_slack_message_tool.execute(
        channel_id=channel_id,
        message=test_message
    )
    send_response = send_result.result

    print("Type of returned send_response:", type(send_response))
    print(f"Send response: {send_response}")

    # Verify that the message was sent successfully
    assert isinstance(send_response, dict), "send_response should be a dict"
    
    # Verify essential Slack API response fields
    assert "ok" in send_response, "Response should have an 'ok' field"
    assert send_response["ok"] is True, "Message send should be successful (ok: true)"
    
    # Check for additional response fields that indicate successful delivery
    expected_fields = ["ts", "channel", "message"]
    for field in expected_fields:
        if field in send_response:
            print(f"Response contains field '{field}': {send_response[field]}")
            
            # Verify channel matches if present
            if field == "channel":
                assert send_response[field] == channel_id, f"Response channel should match requested channel_id"
    
    # Verify at least one of the expected fields is present (indicating proper API response)
    present_fields = [field for field in expected_fields if field in send_response]
    assert len(present_fields) > 0, "Response should contain at least one of: ts, channel, or message"

    print(f"Successfully sent message to Slack channel {channel_id}")
    print(f"Response structure: {send_response}")

    return True