# 3-test_query_target_options.py

async def test_data_source_enumeration_options(zerg_state=None):
    """Test Cisco Stealthwatch data source enumeration by way of query target options"""
    print("Attempting to connect to Cisco Stealthwatch APIs using Cisco Stealthwatch connector")

    assert zerg_state, "this test requires valid zerg_state"

    cisco_stealthwatch_api_url = zerg_state.get("cisco_stealthwatch_api_url").get("value")
    cisco_stealthwatch_username = zerg_state.get("cisco_stealthwatch_username").get("value")
    cisco_stealthwatch_password = zerg_state.get("cisco_stealthwatch_password").get("value")

    from connectors.cisco_stealthwatch.config import CiscoStealthwatchConnectorConfig
    from connectors.cisco_stealthwatch.connector import CiscoStealthwatchConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = CiscoStealthwatchConnectorConfig(
        api_url=cisco_stealthwatch_api_url,
        username=cisco_stealthwatch_username,
        password=cisco_stealthwatch_password,
    )
    assert isinstance(config, ConnectorConfig), "CiscoStealthwatchConnectorConfig should be of type ConnectorConfig"

    connector = CiscoStealthwatchConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CiscoStealthwatchConnector should be of type Connector"

    cisco_stealthwatch_query_target_options = await connector.get_query_target_options()
    assert isinstance(cisco_stealthwatch_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert cisco_stealthwatch_query_target_options, "Failed to retrieve query target options"

    print(f"Cisco Stealthwatch query target option definitions: {cisco_stealthwatch_query_target_options.definitions}")
    print(f"Cisco Stealthwatch query target option selectors: {cisco_stealthwatch_query_target_options.selectors}")

    # Verify that data sources are available
    data_source_selector = None
    for selector in cisco_stealthwatch_query_target_options.selectors:
        if selector.type == 'data_sources':
            data_source_selector = selector
            break

    assert data_source_selector, "Failed to find data_sources selector in query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    assert len(data_source_selector.values) > 0, "data_source_selector should have available data sources"

    # Verify expected data sources are present
    expected_sources = ["flows", "security_events", "alarms"]
    available_sources = data_source_selector.values
    
    for expected in expected_sources:
        source_found = any(expected.lower() in source.lower() for source in available_sources)
        assert source_found, f"Expected data source '{expected}' not found in available sources: {available_sources}"

    return True