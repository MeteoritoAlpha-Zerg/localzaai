# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully verify its connection"""
    print("Testing Reach SOAR connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    reach_soar_api_token = zerg_state.get("reach_soar_api_token").get("value")
    reach_soar_base_url = zerg_state.get("reach_soar_base_url").get("value")
    reach_soar_tenant_id = zerg_state.get("reach_soar_tenant_id").get("value")

    from connectors.reach_soar.config import ReachSOARConnectorConfig
    from connectors.reach_soar.connector import ReachSOARConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = ReachSOARConnectorConfig(
        api_token=reach_soar_api_token,
        base_url=reach_soar_base_url,
        tenant_id=reach_soar_tenant_id,
    )
    assert isinstance(config, ConnectorConfig), "ReachSOARConnectorConfig should be of type ConnectorConfig"

    connector = ReachSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ReachSOARConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True