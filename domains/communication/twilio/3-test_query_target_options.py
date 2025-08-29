# 3-test_query_target_options.py

async def test_phone_number_enumeration_options(zerg_state=None):
    """Test Twilio phone number enumeration by way of query target options"""
    print("Attempting to authenticate using Twilio connector")

    assert zerg_state, "this test requires valid zerg_state"

    twilio_account_sid = zerg_state.get("twilio_account_sid").get("value")
    twilio_auth_token = zerg_state.get("twilio_auth_token").get("value")
    twilio_api_base_url = zerg_state.get("twilio_api_base_url").get("value")

    from connectors.twilio.config import TwilioConnectorConfig
    from connectors.twilio.connector import TwilioConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = TwilioConnectorConfig(
        account_sid=twilio_account_sid,
        auth_token=twilio_auth_token,
        api_base_url=twilio_api_base_url,
    )
    assert isinstance(config, ConnectorConfig), "TwilioConnectorConfig should be of type ConnectorConfig"

    connector = TwilioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "TwilioConnectorConfig should be of type ConnectorConfig"

    twilio_query_target_options = await connector.get_query_target_options()
    assert isinstance(twilio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert twilio_query_target_options, "Failed to retrieve query target options"

    print(f"twilio query target option definitions: {twilio_query_target_options.definitions}")
    print(f"twilio query target option selectors: {twilio_query_target_options.selectors}")

    return True