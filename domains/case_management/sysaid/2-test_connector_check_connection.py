# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid list of tools"""
    print("Testing sysaid connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    sysaid_url = zerg_state.get("sysaid_url").get("value")
    sysaid_account_id = zerg_state.get("sysaid_account_id").get("value")
    sysaid_username = zerg_state.get("sysaid_username").get("value")
    sysaid_password = zerg_state.get("sysaid_password").get("value")

    from connectors.sysaid.config import SysAidConnectorConfig
    from connectors.sysaid.connector import SysAidConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = SysAidConnectorConfig(
        url=sysaid_url,
        account_id=sysaid_account_id,
        username=sysaid_username,
        password=sysaid_password,
    )
    assert isinstance(config, ConnectorConfig), "SysAidConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = SysAidConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SysAidConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True