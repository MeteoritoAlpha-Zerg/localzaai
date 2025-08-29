# 4-test_list_channels.py

async def test_list_channels(zerg_state=None):
    """Test Slack channel enumeration by way of query target options"""
    print("Attempting to authenticate using Slack connector")

    assert zerg_state, "this test requires valid zerg_state"

    slack_bot_token = zerg_state.get("slack_bot_token").get("value")
    slack_workspace_url = zerg_state.get("slack_workspace_url").get("value")

    from connectors.slack.config import SlackConnectorConfig
    from connectors.slack.connector import SlackConnector
    from connectors.slack.tools import SlackConnectorTools
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

    # select channels to target
    channel_selector = None
    for selector in slack_query_target_options.selectors:
        if selector.type == 'channel_ids':  
            channel_selector = selector
            break

    assert channel_selector, "failed to retrieve channel selector from query target options"

    # grab the first two channels 
    num_channels = 2
    assert isinstance(channel_selector.values, list), "channel_selector values must be a list"
    channel_ids = channel_selector.values[:num_channels] if channel_selector.values else None
    print(f"Selecting channel ids: {channel_ids}")

    assert channel_ids, f"failed to retrieve {num_channels} channel ids from channel selector"

    # set up the target with channel ids
    target = SlackTarget(channel_ids=channel_ids)
    assert isinstance(target, ConnectorTargetInterface), "SlackTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_slack_channels tool
    slack_get_channels_tool = next(tool for tool in tools if tool.name == "get_slack_channels")
    slack_channels_result = await slack_get_channels_tool.execute()
    slack_channels = slack_channels_result.result

    print("Type of returned slack_channels:", type(slack_channels))
    print(f"len channels: {len(slack_channels)} channels: {str(slack_channels)[:200]}")

    # ensure that slack_channels are a list of objects with the id being the channel id
    # and the object having the channel name and other relevant information from the slack specification
    # as may be descriptive
    # Verify that slack_channels is a list
    assert isinstance(slack_channels, list), "slack_channels should be a list"
    assert len(slack_channels) > 0, "slack_channels should not be empty"
    assert len(slack_channels) == num_channels, f"slack_channels should have {num_channels} entries"
    
    # Verify structure of each channel object
    for channel in slack_channels:
        assert "id" in channel, "Each channel should have an 'id' field"
        assert channel["id"] in channel_ids, f"Channel id {channel['id']} is not in the requested channel_ids"
        
        # Verify essential Slack channel fields
        # These are common fields in Slack channels based on Slack API specification
        assert "name" in channel, "Each channel should have a 'name' field"
        assert "is_channel" in channel or "is_group" in channel or "is_im" in channel, "Each channel should have a channel type field"
        
        # Check for additional descriptive fields (optional in some Slack instances)
        descriptive_fields = ["topic", "purpose", "is_private", "is_archived", "created", "creator", "num_members"]
        present_fields = [field for field in descriptive_fields if field in channel]
        
        print(f"Channel {channel['id']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if channel == slack_channels[0]:
            print(f"Example channel structure: {channel}")

    print(f"Successfully retrieved and validated {len(slack_channels)} Slack channels")

    return True