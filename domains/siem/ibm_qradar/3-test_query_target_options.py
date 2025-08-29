# 3-test_query_target_options.py

async def test_data_source_enumeration_options(zerg_state=None):
    """Test IBM QRadar data source enumeration by way of query target options"""
    print("Attempting to connect to IBM QRadar APIs using IBM QRadar connector")

    assert zerg_state, "this test requires valid zerg_state"

    ibm_qradar_api_url = zerg_state.get("ibm_qradar_api_url").get("value")
    ibm_qradar_api_token = zerg_state.get("ibm_qradar_api_token").get("value")

    from connectors.ibm_qradar.config import IBMQRadarConnectorConfig
    from connectors.ibm_qradar.connector import IBMQRadarConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = IBMQRadarConnectorConfig(
        api_url=ibm_qradar_api_url,
        api_token=ibm_qradar_api_token,
    )
    assert isinstance(config, ConnectorConfig), "IBMQRadarConnectorConfig should be of type ConnectorConfig"

    connector = IBMQRadarConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "IBMQRadarConnector should be of type Connector"

    ibm_qradar_query_target_options = await connector.get_query_target_options()
    assert isinstance(ibm_qradar_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert ibm_qradar_query_target_options, "Failed to retrieve query target options"

    print(f"IBM QRadar query target option definitions: {ibm_qradar_query_target_options.definitions}")
    print(f"IBM QRadar query target option selectors: {ibm_qradar_query_target_options.selectors}")

    # Verify that data sources are available
    data_source_selector = None
    for selector in ibm_qradar_query_target_options.selectors:
        if selector.type == 'data_sources':
            data_source_selector = selector
            break

    assert data_source_selector, "Failed to find data_sources selector in query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    assert len(data_source_selector.values) > 0, "data_source_selector should have available data sources"

    # Verify expected data sources are present
    expected_sources = ["offenses", "events", "flows"]
    available_sources = data_source_selector.values
    
    for expected in expected_sources:
        source_found = any(expected.lower() in source.lower() for source in available_sources)
        assert source_found, f"Expected data source '{expected}' not found in available sources: {available_sources}"

    return True