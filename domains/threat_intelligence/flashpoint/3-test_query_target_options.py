# 3-test_query_target_options.py

async def test_data_source_enumeration_options(zerg_state=None):
    """Test Flashpoint data source enumeration by way of query target options"""
    print("Attempting to connect to Flashpoint APIs using Flashpoint connector")

    assert zerg_state, "this test requires valid zerg_state"

    flashpoint_api_url = zerg_state.get("flashpoint_api_url").get("value")
    flashpoint_api_key = zerg_state.get("flashpoint_api_key").get("value")

    from connectors.flashpoint.config import FlashpointConnectorConfig
    from connectors.flashpoint.connector import FlashpointConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = FlashpointConnectorConfig(
        api_url=flashpoint_api_url,
        api_key=flashpoint_api_key,
    )
    assert isinstance(config, ConnectorConfig), "FlashpointConnectorConfig should be of type ConnectorConfig"

    connector = FlashpointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "FlashpointConnector should be of type Connector"

    flashpoint_query_target_options = await connector.get_query_target_options()
    assert isinstance(flashpoint_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert flashpoint_query_target_options, "Failed to retrieve query target options"

    print(f"Flashpoint query target option definitions: {flashpoint_query_target_options.definitions}")
    print(f"Flashpoint query target option selectors: {flashpoint_query_target_options.selectors}")

    # Verify that data sources are available
    data_source_selector = None
    for selector in flashpoint_query_target_options.selectors:
        if selector.type == 'data_sources':
            data_source_selector = selector
            break

    assert data_source_selector, "Failed to find data_sources selector in query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    assert len(data_source_selector.values) > 0, "data_source_selector should have available data sources"

    # Verify expected data sources are present
    expected_sources = ["alerts", "indicators", "reports"]
    available_sources = data_source_selector.values
    
    for expected in expected_sources:
        source_found = any(expected.lower() in source.lower() for source in available_sources)
        assert source_found, f"Expected data source '{expected}' not found in available sources: {available_sources}"

    return True