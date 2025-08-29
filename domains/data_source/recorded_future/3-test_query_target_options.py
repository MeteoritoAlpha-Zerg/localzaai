# 3-test_query_target_options.py

async def test_intelligence_source_enumeration_options(zerg_state=None):
    """Test Recorded Future intelligence source enumeration by way of query target options"""
    print("Attempting to connect to Recorded Future APIs using Recorded Future connector")

    assert zerg_state, "this test requires valid zerg_state"

    rf_api_url = zerg_state.get("recorded_future_api_url").get("value")
    rf_api_token = zerg_state.get("recorded_future_api_token").get("value")

    from connectors.recorded_future.config import RecordedFutureConnectorConfig
    from connectors.recorded_future.connector import RecordedFutureConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = RecordedFutureConnectorConfig(
        api_url=rf_api_url,
        api_token=rf_api_token,
    )
    assert isinstance(config, ConnectorConfig), "RecordedFutureConnectorConfig should be of type ConnectorConfig"

    connector = RecordedFutureConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RecordedFutureConnector should be of type Connector"

    rf_query_target_options = await connector.get_query_target_options()
    assert isinstance(rf_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert rf_query_target_options, "Failed to retrieve query target options"

    print(f"Recorded Future query target option definitions: {rf_query_target_options.definitions}")
    print(f"Recorded Future query target option selectors: {rf_query_target_options.selectors}")

    # Verify that intelligence sources are available
    intelligence_source_selector = None
    for selector in rf_query_target_options.selectors:
        if selector.type == 'intelligence_sources':
            intelligence_source_selector = selector
            break

    assert intelligence_source_selector, "Failed to find intelligence_sources selector in query target options"
    assert isinstance(intelligence_source_selector.values, list), "intelligence_source_selector values must be a list"
    assert len(intelligence_source_selector.values) > 0, "intelligence_source_selector should have available intelligence sources"

    # Verify expected intelligence sources are present
    expected_sources = ["indicators", "vulnerabilities", "threat_actors"]
    available_sources = intelligence_source_selector.values
    
    for expected in expected_sources:
        source_found = any(expected.lower() in source.lower() for source in available_sources)
        assert source_found, f"Expected intelligence source '{expected}' not found in available sources: {available_sources}"

    return True