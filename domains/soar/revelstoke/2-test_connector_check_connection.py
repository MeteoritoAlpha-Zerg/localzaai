# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing revelstoke connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    revelstoke_url = zerg_state.get("revelstoke_url").get("value")
    revelstoke_api_key = zerg_state.get("revelstoke_api_key", {}).get("value")
    revelstoke_username = zerg_state.get("revelstoke_username", {}).get("value")
    revelstoke_password = zerg_state.get("revelstoke_password", {}).get("value")
    revelstoke_tenant_id = zerg_state.get("revelstoke_tenant_id", {}).get("value")

    from connectors.revelstoke.config import RevelstokeSoarConnectorConfig
    from connectors.revelstoke.connector import RevelstokeSoarConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    # prefer API key over username/password
    if revelstoke_api_key:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            api_key=revelstoke_api_key,
            tenant_id=revelstoke_tenant_id,
        )
    elif revelstoke_username and revelstoke_password:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            username=revelstoke_username,
            password=revelstoke_password,
            tenant_id=revelstoke_tenant_id,
        )
    else:
        raise Exception("Either revelstoke_api_key or both revelstoke_username and revelstoke_password must be provided")

    assert isinstance(config, ConnectorConfig), "RevelstokeSoarConnectorConfig should be of type ConnectorConfig"

    connector = RevelstokeSoarConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RevelstokeSoarConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True