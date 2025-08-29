# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing twilio connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    twilio_account_sid = zerg_state.get("twilio_account_sid").get("value")
    twilio_auth_token = zerg_state.get("twilio_auth_token").get("value")
    twilio_api_base_url = zerg_state.get("twilio_api_base_url").get("value")

    from connectors.twilio.config import TwilioConnectorConfig
    from connectors.twilio.connector import TwilioConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = TwilioConnectorConfig(
        account_sid=twilio_account_sid,
        auth_token=twilio_auth_token,
        api_base_url=twilio_api_base_url,
    )
    assert isinstance(config, ConnectorConfig), "TwilioConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = TwilioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TwilioConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True