# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to Siemplify (Chronicle SOAR)"""
    print("Testing Siemplify (Chronicle SOAR) connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    siemplify_server_url = zerg_state.get("siemplify_server_url").get("value")
    siemplify_api_token = zerg_state.get("siemplify_api_token").get("value")
    siemplify_user_name = zerg_state.get("siemplify_user_name").get("value")

    from connectors.siemplify.config import SimemplifyConnectorConfig
    from connectors.siemplify.connector import SimemplifyConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = SimemplifyConnectorConfig(
        server_url=siemplify_server_url,
        api_token=siemplify_api_token,
        user_name=siemplify_user_name,
    )
    assert isinstance(config, ConnectorConfig), "SimemplifyConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = SimemplifyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SimemplifyConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True