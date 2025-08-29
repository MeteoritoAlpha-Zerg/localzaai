# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully verify its connection"""
    print("Testing eMASS connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    emass_api_key = zerg_state.get("emass_api_key").get("value")
    emass_api_key_id = zerg_state.get("emass_api_key_id").get("value")
    emass_base_url = zerg_state.get("emass_base_url").get("value")
    emass_client_cert_path = zerg_state.get("emass_client_cert_path").get("value")
    emass_client_key_path = zerg_state.get("emass_client_key_path").get("value")

    from connectors.emass.config import eMASSConnectorConfig
    from connectors.emass.connector import eMASSConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = eMASSConnectorConfig(
        api_key=emass_api_key,
        api_key_id=emass_api_key_id,
        base_url=emass_base_url,
        client_cert_path=emass_client_cert_path,
        client_key_path=emass_client_key_path,
    )
    assert isinstance(config, ConnectorConfig), "eMASSConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = eMASSConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "eMASSConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True