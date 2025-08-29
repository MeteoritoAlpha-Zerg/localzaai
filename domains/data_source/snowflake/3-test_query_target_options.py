# 3-test_query_target_options.py

async def test_project_enumeration_options(zerg_state=None):
    """Test JIRA project enumeration by way of query target options"""
    print("Attempting to authenticate using JIRA connector")

    assert zerg_state, "this test requires valid zerg_state"

    snowflake_account_id = zerg_state.get("snowflake_account_id").get("value")
    snowflake_user = zerg_state.get("snowflake_user").get("value")
    snowflake_password = zerg_state.get("snowflake_password").get("value")

    from connectors.snowflake.config import SnowflakeConnectorConfig
    from connectors.snowflake.connector import SnowflakeConnector

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SnowflakeConnectorConfig(
        account_id=snowflake_account_id,
        user=snowflake_user,
        password=snowflake_password
    )
    assert isinstance(config, ConnectorConfig), "SnowflakeConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SnowflakeConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SnowflakeConnector should be of type Connector"

    query_target_options = await connector.get_query_target_options()
    assert isinstance(query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert query_target_options, "Failed to retrieve query target options"

    print(f"snowflake query target option definitions: {query_target_options.definitions}")
    print(f"snowflake query target option selectors: {query_target_options.selectors}")

    return True