# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to RunZero APIs"""
    print("Testing RunZero connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    runzero_api_url = zerg_state.get("runzero_api_url").get("value")
    runzero_api_token = zerg_state.get("runzero_api_token").get("value")
    runzero_organization_id = zerg_state.get("runzero_organization_id").get("value")

    from connectors.runzero.config import RunZeroConnectorConfig
    from connectors.runzero.connector import RunZeroConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = RunZeroConnectorConfig(
        api_url=runzero_api_url,
        api_token=runzero_api_token,
        organization_id=runzero_organization_id,
    )
    assert isinstance(config, ConnectorConfig), "RunZeroConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = RunZeroConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RunZeroConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True