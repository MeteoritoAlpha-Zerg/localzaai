# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector can successfully verify its connection"""
    print("Testing DomainTools connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    domaintools_api_username = zerg_state.get("domaintools_api_username").get("value")
    domaintools_api_key = zerg_state.get("domaintools_api_key").get("value")
    domaintools_base_url = zerg_state.get("domaintools_base_url").get("value")

    from connectors.domaintools.config import DomainToolsConnectorConfig
    from connectors.domaintools.connector import DomainToolsConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    config = DomainToolsConnectorConfig(
        api_username=domaintools_api_username,
        api_key=domaintools_api_key,
        base_url=domaintools_base_url,
    )
    assert isinstance(config, ConnectorConfig), "DomainToolsConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = DomainToolsConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DomainToolsConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True