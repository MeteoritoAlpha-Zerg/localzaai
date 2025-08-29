# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state = None):
    """Test whether connector returns a valid list of tools"""
    print("Testing confluence connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    confluence_url = zerg_state.get("confluence_url").get("value")
    confluence_api_token = zerg_state.get("confluence_api_token").get("value")
    confluence_email = zerg_state.get("confluence_email").get("value")

    from connectors.confluence.config import ConfluenceConnectorConfig
    from connectors.confluence.connector import ConfluenceConnector
    from connectors.confluence.target import ConfluenceTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = ConfluenceConnectorConfig(
        url=confluence_url,
        api_token=confluence_api_token,
        email=confluence_email,
    )
    assert isinstance(config, ConnectorConfig), "ConfluenceConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ConfluenceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ConfluenceConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True