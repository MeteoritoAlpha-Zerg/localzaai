# 3-test_query_target_options.py

async def test_data_source_enumeration_options(zerg_state=None):
    """Test Splunk Phantom data source enumeration by way of query target options"""
    print("Attempting to connect to Splunk Phantom APIs using Splunk Phantom connector")

    assert zerg_state, "this test requires valid zerg_state"

    splunk_phantom_api_url = zerg_state.get("splunk_phantom_api_url").get("value")
    splunk_phantom_api_token = zerg_state.get("splunk_phantom_api_token").get("value")

    from connectors.splunk_phantom.config import SplunkPhantomConnectorConfig
    from connectors.splunk_phantom.connector import SplunkPhantomConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SplunkPhantomConnectorConfig(
        api_url=splunk_phantom_api_url,
        api_token=splunk_phantom_api_token,
    )
    assert isinstance(config, ConnectorConfig), "SplunkPhantomConnectorConfig should be of type ConnectorConfig"

    connector = SplunkPhantomConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SplunkPhantomConnector should be of type Connector"

    splunk_phantom_query_target_options = await connector.get_query_target_options()
    assert isinstance(splunk_phantom_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert splunk_phantom_query_target_options, "Failed to retrieve query target options"

    print(f"Splunk Phantom query target option definitions: {splunk_phantom_query_target_options.definitions}")
    print(f"Splunk Phantom query target option selectors: {splunk_phantom_query_target_options.selectors}")

    # Verify that data sources are available
    data_source_selector = None
    for selector in splunk_phantom_query_target_options.selectors:
        if selector.type == 'data_sources':
            data_source_selector = selector
            break

    assert data_source_selector, "Failed to find data_sources selector in query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    assert len(data_source_selector.values) > 0, "data_source_selector should have available data sources"

    # Verify expected data sources are present
    expected_sources = ["containers", "playbooks", "actions"]
    available_sources = data_source_selector.values
    
    for expected in expected_sources:
        source_found = any(expected.lower() in source.lower() for source in available_sources)
        assert source_found, f"Expected data source '{expected}' not found in available sources: {available_sources}"

    return True