# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing discord connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    discord_bot_token = zerg_state.get("discord_bot_token").get("value")
    discord_api_base_url = zerg_state.get("discord_api_base_url").get("value")
    discord_api_version = zerg_state.get("discord_api_version").get("value")

    from connectors.discord.config import DiscordConnectorConfig
    from connectors.discord.connector import DiscordConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = DiscordConnectorConfig(
        bot_token=discord_bot_token,
        api_base_url=discord_api_base_url,
        api_version=discord_api_version,
    )
    assert isinstance(config, ConnectorConfig), "DiscordConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = DiscordConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DiscordConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True