# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to CISA APIs"""
    print("Testing CISA connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    cisa_base_url = zerg_state.get("cisa_base_url").get("value")
    cisa_kev_url = zerg_state.get("cisa_kev_url").get("value")

    from connectors.cisa.config import CISAConnectorConfig
    from connectors.cisa.connector import CISAConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = CISAConnectorConfig(
        base_url=cisa_base_url,
        kev_url=cisa_kev_url,
    )
    assert isinstance(config, ConnectorConfig), "CISAConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = CISAConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CISAConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True