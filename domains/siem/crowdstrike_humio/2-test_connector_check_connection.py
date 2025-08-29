# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully verify its connection"""
    print("Testing CrowdStrike Humio connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    humio_api_token = zerg_state.get("humio_api_token").get("value")
    humio_base_url = zerg_state.get("humio_base_url").get("value")
    humio_organization = zerg_state.get("humio_organization").get("value")

    from connectors.crowdstrike_humio.config import CrowdStrikeHumioConnectorConfig
    from connectors.crowdstrike_humio.connector import CrowdStrikeHumioConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = CrowdStrikeHumioConnectorConfig(
        api_token=humio_api_token,
        base_url=humio_base_url,
        organization=humio_organization,
    )
    assert isinstance(config, ConnectorConfig), "CrowdStrikeHumioConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = CrowdStrikeHumioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CrowdStrikeHumioConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True