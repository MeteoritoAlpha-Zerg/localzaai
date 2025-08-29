# 3-test_query_target_options.py

async def test_index_enumeration_options(zerg_state=None):
    """Test Elasticsearch index enumeration by way of query target options"""
    print("Attempting to authenticate using Elastic connector")

    assert zerg_state, "this test requires valid zerg_state"

    elastic_url = zerg_state.get("elastic_url").get("value")
    elastic_api_key = zerg_state.get("elastic_api_key").get("value")
    elastic_username = zerg_state.get("elastic_username", {}).get("value")
    elastic_password = zerg_state.get("elastic_password", {}).get("value")

    from connectors.elastic.config import ElasticConnectorConfig
    from connectors.elastic.connector import ElasticConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
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

    connector = ElasticConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ElasticConnector should be of type Connector"

    elastic_query_target_options = await connector.get_query_target_options()
    assert isinstance(elastic_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert elastic_query_target_options, "Failed to retrieve query target options"

    print(f"elastic query target option definitions: {elastic_query_target_options.definitions}")
    print(f"elastic query target option selectors: {elastic_query_target_options.selectors}")

    return True