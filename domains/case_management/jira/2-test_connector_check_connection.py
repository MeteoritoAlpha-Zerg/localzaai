# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing jira connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    jira_url = zerg_state.get("jira_url").get("value")
    jira_api_token = zerg_state.get("jira_api_token").get("value")
    jira_email = zerg_state.get("jira_email").get("value")

    from connectors.jira.config import JIRAConnectorConfig
    from connectors.jira.connector import JIRAConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = JIRAConnectorConfig(
        url=jira_url,
        api_token=jira_api_token,
        email=jira_email,
    )
    assert isinstance(config, ConnectorConfig), "JIRAConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = JIRAConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "JIRAConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True