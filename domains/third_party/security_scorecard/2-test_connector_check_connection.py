# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to SecurityScorecard APIs"""
    print("Testing SecurityScorecard connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    securityscorecard_api_url = zerg_state.get("securityscorecard_api_url").get("value")
    securityscorecard_api_token = zerg_state.get("securityscorecard_api_token").get("value")

    from connectors.securityscorecard.config import SecurityScorecardConnectorConfig
    from connectors.securityscorecard.connector import SecurityScorecardConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = SecurityScorecardConnectorConfig(
        api_url=securityscorecard_api_url,
        api_token=securityscorecard_api_token,
    )
    assert isinstance(config, ConnectorConfig), "SecurityScorecardConnectorConfig should be of type ConnectorConfig"

    connector = SecurityScorecardConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SecurityScorecardConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True