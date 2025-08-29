# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing slack connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    slack_bot_token = zerg_state.get("slack_bot_token").get("value")
    slack_workspace_url = zerg_state.get("slack_workspace_url").get("value")

    from connectors.slack.config import SlackConnectorConfig
    from connectors.slack.connector import SlackConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = SlackConnectorConfig(
        bot_token=slack_bot_token,
        workspace_url=slack_workspace_url,
    )
    assert isinstance(config, ConnectorConfig), "SlackConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = SlackConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SlackConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True