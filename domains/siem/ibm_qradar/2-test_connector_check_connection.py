# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to IBM QRadar APIs"""
    print("Testing IBM QRadar connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    ibm_qradar_api_url = zerg_state.get("ibm_qradar_api_url").get("value")
    ibm_qradar_api_token = zerg_state.get("ibm_qradar_api_token").get("value")

    from connectors.ibm_qradar.config import IBMQRadarConnectorConfig
    from connectors.ibm_qradar.connector import IBMQRadarConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = IBMQRadarConnectorConfig(
        api_url=ibm_qradar_api_url,
        api_token=ibm_qradar_api_token,
    )
    assert isinstance(config, ConnectorConfig), "IBMQRadarConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = IBMQRadarConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "IBMQRadarConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True