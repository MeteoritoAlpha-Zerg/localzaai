# 4-test_get_kev_data.py

async def test_get_kev_data(zerg_state=None):
    """Test CISA KEV (Known Exploited Vulnerabilities) data retrieval"""
    print("Testing CISA KEV data retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    cisa_base_url = zerg_state.get("cisa_base_url").get("value")
    cisa_kev_url = zerg_state.get("cisa_kev_url").get("value")

    from connectors.cisa.config import CISAConnectorConfig
    from connectors.cisa.connector import CISAConnector
    from connectors.cisa.target import CISATarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = CISAConnectorConfig(
        base_url=cisa_base_url,
        kev_url=cisa_kev_url
    )
    assert isinstance(config, ConnectorConfig), "CISAConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CISAConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CISAConnector should be of type Connector"

    # get query target options
    cisa_query_target_options = await connector.get_query_target_options()
    assert isinstance(cisa_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select KEV data source
    data_source_selector = None
    for selector in cisa_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find KEV in available data sources
    kev_source = None
    for source in data_source_selector.values:
        if 'kev' in source.lower() or 'vulnerability' in source.lower():
            kev_source = source
            break
    
    assert kev_source, "KEV data source not found in available options"
    print(f"Selecting KEV data source: {kev_source}")

    # set up the target with KEV data source
    target = CISATarget(data_sources=[kev_source])
    assert isinstance(target, ConnectorTargetInterface), "CISATarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_cisa_kev tool
    cisa_get_kev_tool = next(tool for tool in tools if tool.name == "get_cisa_kev")
    kev_result = await cisa_get_kev_tool.execute()
    kev_data = kev_result.result

    print("Type of returned KEV data:", type(kev_data))
    print(f"KEV entries count: {len(kev_data)} sample: {str(kev_data)[:200]}")

    # Verify that kev_data is a list
    assert isinstance(kev_data, list), "KEV data should be a list"
    assert len(kev_data) > 0, "KEV data should not be empty"
    
    # Limit the number of entries to check if there are many
    entries_to_check = kev_data[:5] if len(kev_data) > 5 else kev_data
    
    # Verify structure of each KEV entry
    for entry in entries_to_check:
        # Verify essential KEV fields based on CISA KEV catalog structure
        assert "cveID" in entry, "Each KEV entry should have a 'cveID' field"
        assert "vendorProject" in entry, "Each KEV entry should have a 'vendorProject' field"
        assert "product" in entry, "Each KEV entry should have a 'product' field"
        assert "vulnerabilityName" in entry, "Each KEV entry should have a 'vulnerabilityName' field"
        assert "dateAdded" in entry, "Each KEV entry should have a 'dateAdded' field"
        assert "shortDescription" in entry, "Each KEV entry should have a 'shortDescription' field"
        assert "requiredAction" in entry, "Each KEV entry should have a 'requiredAction' field"
        assert "dueDate" in entry, "Each KEV entry should have a 'dueDate' field"
        
        # Verify CVE ID format
        cve_id = entry["cveID"]
        assert cve_id.startswith("CVE-"), f"CVE ID {cve_id} should start with 'CVE-'"
        
        # Log the structure of the first entry for debugging
        if entry == entries_to_check[0]:
            print(f"Example KEV entry structure: {entry}")

    print(f"Successfully retrieved and validated {len(kev_data)} CISA KEV entries")

    return True