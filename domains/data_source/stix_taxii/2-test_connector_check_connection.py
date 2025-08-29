# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully verify its connection"""
    print("Testing STIX/TAXII connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    taxii_server_url = zerg_state.get("taxii_server_url").get("value")
    taxii_username = zerg_state.get("taxii_username").get("value")
    taxii_password = zerg_state.get("taxii_password").get("value")

    from connectors.stix_taxii.config import STIXTAXIIConnectorConfig
    from connectors.stix_taxii.connector import STIXTAXIIConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = STIXTAXIIConnectorConfig(
        server_url=taxii_server_url,
        username=taxii_username,
        password=taxii_password,
    )
    assert isinstance(config, ConnectorConfig), "STIXTAXIIConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = STIXTAXIIConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "STIXTAXIIConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True