# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully connect to Rapid7 InsightIDR APIs"""
    print("Testing Rapid7 InsightIDR connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    rapid7_insightidr_api_url = zerg_state.get("rapid7_insightidr_api_url").get("value")
    rapid7_insightidr_api_key = zerg_state.get("rapid7_insightidr_api_key").get("value")

    from connectors.rapid7_insightidr.config import Rapid7InsightIDRConnectorConfig
    from connectors.rapid7_insightidr.connector import Rapid7InsightIDRConnector
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = Rapid7InsightIDRConnectorConfig(
        api_url=rapid7_insightidr_api_url,
        api_key=rapid7_insightidr_api_key,
    )
    assert isinstance(config, ConnectorConfig), "Rapid7InsightIDRConnectorConfig should be of type ConnectorConfig"

    connector = Rapid7InsightIDRConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "Rapid7InsightIDRConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True