# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to RSA Archer APIs"""
    print("Testing RSA Archer connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    rsa_archer_api_url = zerg_state.get("rsa_archer_api_url").get("value")
    rsa_archer_username = zerg_state.get("rsa_archer_username").get("value")
    rsa_archer_password = zerg_state.get("rsa_archer_password").get("value")
    rsa_archer_instance_name = zerg_state.get("rsa_archer_instance_name").get("value")

    from connectors.rsa_archer.config import RSAArcherConnectorConfig
    from connectors.rsa_archer.connector import RSAArcherConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = RSAArcherConnectorConfig(
        api_url=rsa_archer_api_url,
        username=rsa_archer_username,
        password=rsa_archer_password,
        instance_name=rsa_archer_instance_name,
    )
    assert isinstance(config, ConnectorConfig), "RSAArcherConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = RSAArcherConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RSAArcherConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True