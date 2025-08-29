# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to OpenDNS (Cisco Umbrella)"""
    print("Testing OpenDNS (Cisco Umbrella) connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    opendns_api_key = zerg_state.get("opendns_api_key").get("value")
    opendns_api_secret = zerg_state.get("opendns_api_secret").get("value")
    opendns_organization_id = zerg_state.get("opendns_organization_id").get("value")

    from connectors.opendns.config import OpenDNSConnectorConfig
    from connectors.opendns.connector import OpenDNSConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = OpenDNSConnectorConfig(
        api_key=opendns_api_key,
        api_secret=opendns_api_secret,
        organization_id=opendns_organization_id,
    )
    assert isinstance(config, ConnectorConfig), "OpenDNSConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = OpenDNSConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "OpenDNSConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True