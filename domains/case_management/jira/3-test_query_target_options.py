# 3-test_query_target_options.py

async def test_project_enumeration_options(zerg_state=None):
    """Test JIRA project enumeration by way of query target options"""
    print("Attempting to authenticate using JIRA connector")

    assert zerg_state, "this test requires valid zerg_state"

    jira_url = zerg_state.get("jira_url").get("value")
    jira_api_token = zerg_state.get("jira_api_token").get("value")
    jira_email = zerg_state.get("jira_email").get("value")

    from connectors.jira.config import JIRAConnectorConfig
    from connectors.jira.connector import JIRAConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = JIRAConnectorConfig(
        url=jira_url,
        api_token=jira_api_token,
        email=jira_email,
    )
    assert isinstance(config, ConnectorConfig), "JIRAConnectorConfig should be of type ConnectorConfig"

    connector = JIRAConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "JIRAConnectorConfig should be of type ConnectorConfig"

    jira_query_target_options = await connector.get_query_target_options()
    assert isinstance(jira_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert jira_query_target_options, "Failed to retrieve query target options"

    print(f"jira query target option definitions: {jira_query_target_options.definitions}")
    print(f"jira query target option selectors: {jira_query_target_options.selectors}")

    return True