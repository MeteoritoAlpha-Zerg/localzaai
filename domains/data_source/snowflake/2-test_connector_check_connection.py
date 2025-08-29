# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing snowflake connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    snowflake_account_id = zerg_state.get("snowflake_account_id").get("value")
    snowflake_user = zerg_state.get("snowflake_user").get("value")
    snowflake_password = zerg_state.get("snowflake_password").get("value")

    from connectors.snowflake.config import SnowflakeConnectorConfig
    from connectors.snowflake.connector import SnowflakeConnector

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

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

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True