# 3-test_query_target_options.py

async def test_search_index_enumeration_options(zerg_state=None):
    """Test Censys search index enumeration by way of query target options"""
    print("Attempting to authenticate using Censys connector")

    assert zerg_state, "this test requires valid zerg_state"

    censys_api_id = zerg_state.get("censys_api_id").get("value")
    censys_api_secret = zerg_state.get("censys_api_secret").get("value")
    censys_base_url = zerg_state.get("censys_base_url").get("value")

    from connectors.censys.config import CensysConnectorConfig
    from connectors.censys.connector import CensysConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = CensysConnectorConfig(
        api_id=censys_api_id,
        api_secret=censys_api_secret,
        base_url=censys_base_url,
    )
    assert isinstance(config, ConnectorConfig), "CensysConnectorConfig should be of type ConnectorConfig"

    connector = CensysConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CensysConnector should be of type Connector"

    censys_query_target_options = await connector.get_query_target_options()
    assert isinstance(censys_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert censys_query_target_options, "Failed to retrieve query target options"

    print(f"censys query target option definitions: {censys_query_target_options.definitions}")
    print(f"censys query target option selectors: {censys_query_target_options.selectors}")

    return True