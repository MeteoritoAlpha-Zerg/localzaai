# 7-test_list_users.py

async def test_list_users(zerg_state=None):
    """Test Slack user enumeration in workspace"""
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

    # set up the target (no specific targeting needed for user list)
    target = SlackTarget()
    assert isinstance(target, ConnectorTargetInterface), "SlackTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_slack_users tool
    slack_get_users_tool = next(tool for tool in tools if tool.name == "get_slack_users")
    slack_users_result = await slack_get_users_tool.execute()
    slack_users = slack_users_result.result

    print("Type of returned slack_users:", type(slack_users))
    print(f"len users: {len(slack_users)} users: {str(slack_users)[:200]}")

    # Verify that slack_users is a list
    assert isinstance(slack_users, list), "slack_users should be a list"
    assert len(slack_users) > 0, "slack_users should not be empty"
    
    # Limit the number of users to check if there are many
    users_to_check = slack_users[:5] if len(slack_users) > 5 else slack_users
    
    # Verify structure of each user object
    for user in users_to_check:
        # Verify essential Slack user fields
        assert "id" in user, "Each user should have an 'id' field"
        assert "name" in user, "Each user should have a 'name' field"
        assert "deleted" in user, "Each user should have a 'deleted' field"
        
        # Verify profile information is present
        assert "profile" in user, "Each user should have a 'profile' object"
        profile = user["profile"]
        
        # Check for common profile fields
        profile_fields = ["real_name", "display_name", "email", "image_24", "image_32"]
        present_profile_fields = [field for field in profile_fields if field in profile]
        
        print(f"User {user['id']} profile contains these fields: {', '.join(present_profile_fields)}")
        
        # Check for additional optional user fields
        optional_fields = ["is_admin", "is_owner", "is_bot", "updated", "is_app_user"]
        present_optional = [field for field in optional_fields if field in user]
        
        print(f"User {user['id']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first user for debugging
        if user == users_to_check[0]:
            print(f"Example user structure: {user}")

    print(f"Successfully retrieved and validated {len(slack_users)} Slack users")

    return True