# 3-test_query_target_options.py

async def test_collector_enumeration_options(zerg_state=None):
    """Test Sumo Logic collector and source enumeration by way of query target options"""
    print("Attempting to authenticate using Sumo Logic connector")

    assert zerg_state, "this test requires valid zerg_state"

    sumologic_url = zerg_state.get("sumologic_url").get("value")
    sumologic_access_id = zerg_state.get("sumologic_access_id").get("value")
    sumologic_access_key = zerg_state.get("sumologic_access_key").get("value")

    from connectors.sumologic.config import SumoLogicConnectorConfig
    from connectors.sumologic.connector import SumoLogicConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SumoLogicConnectorConfig(
        url=sumologic_url,
        access_id=sumologic_access_id,
        access_key=sumologic_access_key,
    )
    assert isinstance(config, ConnectorConfig), "SumoLogicConnectorConfig should be of type ConnectorConfig"

    connector = SumoLogicConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SumoLogicConnector should be of type Connector"

    sumologic_query_target_options = await connector.get_query_target_options()
    assert isinstance(sumologic_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert sumologic_query_target_options, "Failed to retrieve query target options"

    print(f"sumologic query target option definitions: {sumologic_query_target_options.definitions}")
    print(f"sumologic query target option selectors: {sumologic_query_target_options.selectors}")

    return True