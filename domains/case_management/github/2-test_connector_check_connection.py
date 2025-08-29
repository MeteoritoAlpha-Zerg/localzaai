# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing jira connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    github_api_url = zerg_state.get("github_api_url").get("value")
    github_access_token = zerg_state.get("github_access_token").get("value")

    from connectors.github.config import GithubConnectorConfig
    from connectors.github.connector import GithubConnector

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = GithubConnectorConfig(
        url=github_api_url,
        access_token=github_access_token,
    )
    assert isinstance(config, ConnectorConfig), "GithubConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = GithubConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GithubConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True