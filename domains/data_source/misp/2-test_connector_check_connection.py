# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to MISP"""
    print("Testing MISP connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    misp_url = zerg_state.get("misp_url").get("value")
    misp_api_key = zerg_state.get("misp_api_key").get("value")

    from connectors.misp.config import MISPConnectorConfig
    from connectors.misp.connector import MISPConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = MISPConnectorConfig(
        url=misp_url,
        api_key=misp_api_key,
    )
    assert isinstance(config, ConnectorConfig), "MISPConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = MISPConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MISPConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True