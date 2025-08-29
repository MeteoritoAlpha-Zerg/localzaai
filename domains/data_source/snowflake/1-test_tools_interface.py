# 1-test_tools_interface.py

async def test_tools_interface(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing connector tools interfaces")

    assert zerg_state, "this test requires valid zerg_state"

    snowflake_account_id = zerg_state.get("snowflake_account_id").get("value")
    snowflake_user = zerg_state.get("snowflake_user").get("value")
    snowflake_password = zerg_state.get("snowflake_password").get("value")

    from connectors.snowflake.config import SnowflakeConnectorConfig
    from connectors.snowflake.connector import SnowflakeConnector
    from connectors.snowflake.target import SnowflakeTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface

    from common.models.tool import Tool

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

    target = SnowflakeTarget()
    assert isinstance(target, ConnectorTargetInterface), "SnowflakeTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    for tool in tools:
        assert isinstance(tool, Tool), f"Item {tool} is not an instance of Tool"

    return True