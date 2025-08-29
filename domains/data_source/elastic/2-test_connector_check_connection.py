# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing elastic connector connection")

    assert zerg_state, "this test requires valid zerg_state"

    elastic_url = zerg_state.get("elastic_url").get("value")
    elastic_api_key = zerg_state.get("elastic_api_key").get("value")
    elastic_username = zerg_state.get("elastic_username", {}).get("value")
    elastic_password = zerg_state.get("elastic_password", {}).get("value")

    from connectors.elastic.config import ElasticConnectorConfig
    from connectors.elastic.connector import ElasticConnector
    
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector

    # initialize the connector config - prefer API key over username/password
    if elastic_api_key:
        config = ElasticConnectorConfig(
            url=elastic_url,
            api_key=elastic_api_key,
        )
    elif elastic_username and elastic_password:
        config = ElasticConnectorConfig(
            url=elastic_url,
            username=elastic_username,
            password=elastic_password,
        )
    else:
        raise Exception("Either elastic_api_key or both elastic_username and elastic_password must be provided")

    assert isinstance(config, ConnectorConfig), "ElasticConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = ElasticConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ElasticConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True