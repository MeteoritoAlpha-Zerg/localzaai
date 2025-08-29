# 3-test_query_target_options.py

async def test_data_source_enumeration_options(zerg_state=None):
    """Test CISA data source enumeration by way of query target options"""
    print("Attempting to connect to CISA APIs using CISA connector")

    assert zerg_state, "this test requires valid zerg_state"

    cisa_base_url = zerg_state.get("cisa_base_url").get("value")
    cisa_kev_url = zerg_state.get("cisa_kev_url").get("value")

    from connectors.cisa.config import CISAConnectorConfig
    from connectors.cisa.connector import CISAConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = CISAConnectorConfig(
        base_url=cisa_base_url,
        kev_url=cisa_kev_url,
    )
    assert isinstance(config, ConnectorConfig), "CISAConnectorConfig should be of type ConnectorConfig"

    connector = CISAConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CISAConnector should be of type Connector"

    cisa_query_target_options = await connector.get_query_target_options()
    assert isinstance(cisa_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert cisa_query_target_options, "Failed to retrieve query target options"

    print(f"CISA query target option definitions: {cisa_query_target_options.definitions}")
    print(f"CISA query target option selectors: {cisa_query_target_options.selectors}")

    # Verify that data sources are available
    data_source_selector = None
    for selector in cisa_query_target_options.selectors:
        if selector.type == 'data_sources':
            data_source_selector = selector
            break

    assert data_source_selector, "Failed to find data_sources selector in query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    assert len(data_source_selector.values) > 0, "data_source_selector should have available data sources"

    return True