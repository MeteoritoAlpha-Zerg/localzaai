# 3-test_query_target_options.py

async def test_data_source_enumeration_options(zerg_state=None):
    """Test RunZero data source enumeration by way of query target options"""
    print("Attempting to connect to RunZero APIs using RunZero connector")

    assert zerg_state, "this test requires valid zerg_state"

    runzero_api_url = zerg_state.get("runzero_api_url").get("value")
    runzero_api_token = zerg_state.get("runzero_api_token").get("value")
    runzero_organization_id = zerg_state.get("runzero_organization_id").get("value")

    from connectors.runzero.config import RunZeroConnectorConfig
    from connectors.runzero.connector import RunZeroConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = RunZeroConnectorConfig(
        api_url=runzero_api_url,
        api_token=runzero_api_token,
        organization_id=runzero_organization_id,
    )
    assert isinstance(config, ConnectorConfig), "RunZeroConnectorConfig should be of type ConnectorConfig"

    connector = RunZeroConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RunZeroConnector should be of type Connector"

    runzero_query_target_options = await connector.get_query_target_options()
    assert isinstance(runzero_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert runzero_query_target_options, "Failed to retrieve query target options"

    print(f"RunZero query target option definitions: {runzero_query_target_options.definitions}")
    print(f"RunZero query target option selectors: {runzero_query_target_options.selectors}")

    # Verify that data sources are available
    data_source_selector = None
    for selector in runzero_query_target_options.selectors:
        if selector.type == 'data_sources':
            data_source_selector = selector
            break

    assert data_source_selector, "Failed to find data_sources selector in query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    assert len(data_source_selector.values) > 0, "data_source_selector should have available data sources"

    # Verify expected data sources are present
    expected_sources = ["assets", "services", "scans"]
    available_sources = data_source_selector.values
    
    for expected in expected_sources:
        source_found = any(expected.lower() in source.lower() for source in available_sources)
        assert source_found, f"Expected data source '{expected}' not found in available sources: {available_sources}"

    return True