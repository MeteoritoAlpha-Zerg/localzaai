# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to Cisco Stealthwatch APIs"""
    print("Testing Cisco Stealthwatch connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    cisco_stealthwatch_api_url = zerg_state.get("cisco_stealthwatch_api_url").get("value")
    cisco_stealthwatch_username = zerg_state.get("cisco_stealthwatch_username").get("value")
    cisco_stealthwatch_password = zerg_state.get("cisco_stealthwatch_password").get("value")

    from connectors.cisco_stealthwatch.config import CiscoStealthwatchConnectorConfig
    from connectors.cisco_stealthwatch.connector import CiscoStealthwatchConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = CiscoStealthwatchConnectorConfig(
        api_url=cisco_stealthwatch_api_url,
        username=cisco_stealthwatch_username,
        password=cisco_stealthwatch_password,
    )
    assert isinstance(config, ConnectorConfig), "CiscoStealthwatchConnectorConfig should be of type ConnectorConfig"

    connector = CiscoStealthwatchConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CiscoStealthwatchConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True