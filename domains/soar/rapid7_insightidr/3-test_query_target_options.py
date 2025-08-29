# 3-test_query_target_options.py

async def test_data_source_enumeration_options(zerg_state=None):
    """Test Rapid7 InsightIDR data source enumeration by way of query target options"""
    print("Attempting to connect to Rapid7 InsightIDR APIs using Rapid7 InsightIDR connector")

    assert zerg_state, "this test requires valid zerg_state"

    rapid7_insightidr_api_url = zerg_state.get("rapid7_insightidr_api_url").get("value")
    rapid7_insightidr_api_key = zerg_state.get("rapid7_insightidr_api_key").get("value")

    from connectors.rapid7_insightidr.config import Rapid7InsightIDRConnectorConfig
    from connectors.rapid7_insightidr.connector import Rapid7InsightIDRConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
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

    rapid7_insightidr_query_target_options = await connector.get_query_target_options()
    assert isinstance(rapid7_insightidr_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert rapid7_insightidr_query_target_options, "Failed to retrieve query target options"

    print(f"Rapid7 InsightIDR query target option definitions: {rapid7_insightidr_query_target_options.definitions}")
    print(f"Rapid7 InsightIDR query target option selectors: {rapid7_insightidr_query_target_options.selectors}")

    # Verify that data sources are available
    data_source_selector = None
    for selector in rapid7_insightidr_query_target_options.selectors:
        if selector.type == 'data_sources':
            data_source_selector = selector
            break

    assert data_source_selector, "Failed to find data_sources selector in query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    assert len(data_source_selector.values) > 0, "data_source_selector should have available data sources"

    # Verify expected data sources are present
    expected_sources = ["investigations", "logs", "assets"]
    available_sources = data_source_selector.values
    
    for expected in expected_sources:
        source_found = any(expected.lower() in source.lower() for source in available_sources)
        assert source_found, f"Expected data source '{expected}' not found in available sources: {available_sources}"

    return True