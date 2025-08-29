# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to Cortex XSIAM APIs"""
    print("Testing Cortex XSIAM connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    cortex_xsiam_api_url = zerg_state.get("cortex_xsiam_api_url").get("value")
    cortex_xsiam_api_key = zerg_state.get("cortex_xsiam_api_key").get("value")
    cortex_xsiam_api_key_id = zerg_state.get("cortex_xsiam_api_key_id").get("value")
    cortex_xsiam_tenant_id = zerg_state.get("cortex_xsiam_tenant_id").get("value")

    from connectors.cortex_xsiam.config import CortexXSIAMConnectorConfig
    from connectors.cortex_xsiam.connector import CortexXSIAMConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = CortexXSIAMConnectorConfig(
        api_url=cortex_xsiam_api_url,
        api_key=cortex_xsiam_api_key,
        api_key_id=cortex_xsiam_api_key_id,
        tenant_id=cortex_xsiam_tenant_id,
    )
    assert isinstance(config, ConnectorConfig), "CortexXSIAMConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = CortexXSIAMConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CortexXSIAMConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True