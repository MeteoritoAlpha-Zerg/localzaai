# 3-test_query_target_options.py

async def test_channel_enumeration_options(zerg_state=None):
    """Test Slack channel enumeration by way of query target options"""
    print("Attempting to authenticate using Slack connector")

    assert zerg_state, "this test requires valid zerg_state"

    slack_bot_token = zerg_state.get("slack_bot_token").get("value")
    slack_workspace_url = zerg_state.get("slack_workspace_url").get("value")

    from connectors.slack.config import SlackConnectorConfig
    from connectors.slack.connector import SlackConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SlackConnectorConfig(
        bot_token=slack_bot_token,
        workspace_url=slack_workspace_url,
    )
    assert isinstance(config, ConnectorConfig), "SlackConnectorConfig should be of type ConnectorConfig"

    connector = SlackConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SlackConnectorConfig should be of type ConnectorConfig"

    slack_query_target_options = await connector.get_query_target_options()
    assert isinstance(slack_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert slack_query_target_options, "Failed to retrieve query target options"

    print(f"slack query target option definitions: {slack_query_target_options.definitions}")
    print(f"slack query target option selectors: {slack_query_target_options.selectors}")

    return True