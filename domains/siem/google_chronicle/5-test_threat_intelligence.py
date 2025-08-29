# 5-test_threat_intelligence.py

async def test_threat_intelligence(zerg_state=None):
    """Test Google Chronicle threat intelligence and IoC data retrieval"""
    print("Attempting to retrieve threat intelligence using Google Chronicle connector")

    assert zerg_state, "this test requires valid zerg_state"

    chronicle_service_account_path = zerg_state.get("chronicle_service_account_path").get("value")
    chronicle_customer_id = zerg_state.get("chronicle_customer_id").get("value")

    from connectors.chronicle.config import ChronicleConnectorConfig
    from connectors.chronicle.connector import ChronicleConnector
    from connectors.chronicle.tools import ChronicleConnectorTools, GetIoCDataInput
    from connectors.chronicle.target import ChronicleTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ChronicleConnectorConfig(
        service_account_path=chronicle_service_account_path,
        customer_id=chronicle_customer_id
    )
    assert isinstance(config, ConnectorConfig), "ChronicleConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ChronicleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ChronicleConnector should be of type Connector"

    # get query target options
    chronicle_query_target_options = await connector.get_query_target_options()
    assert isinstance(chronicle_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select data sources to target
    data_source_selector = None
    for selector in chronicle_query_target_options.selectors:
        if selector.type == 'data_source_ids':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"

    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    data_source_id = data_source_selector.values[0] if data_source_selector.values else None
    print(f"Selecting data source ID: {data_source_id}")

    assert data_source_id, f"failed to retrieve data source ID from data source selector"

    # set up the target with data source ID
    target = ChronicleTarget(data_source_ids=[data_source_id])
    assert isinstance(target, ConnectorTargetInterface), "ChronicleTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_ioc_data tool and execute it with test IoCs
    get_ioc_data_tool = next(tool for tool in tools if tool.name == "get_ioc_data")
    test_iocs = ["8.8.8.8", "google.com", "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"]
    ioc_data_result = await get_ioc_data_tool.execute(indicators=test_iocs)
    ioc_data = ioc_data_result.result

    print("Type of returned ioc_data:", type(ioc_data))
    print(f"IoC data: {str(ioc_data)[:200]}")

    # Verify that ioc_data is a dictionary or list
    assert isinstance(ioc_data, (dict, list)), "ioc_data should be a dictionary or list"
    
    if isinstance(ioc_data, dict):
        # If it's a dictionary, check each IoC
        for ioc in test_iocs:
            if ioc in ioc_data:
                ioc_info = ioc_data[ioc]
                assert "artifact" in ioc_info, f"IoC {ioc} should have 'artifact' field"
                assert "sources" in ioc_info, f"IoC {ioc} should have 'sources' field"
                
                print(f"IoC {ioc} found with {len(ioc_info.get('sources', []))} threat intelligence sources")
    else:
        # If it's a list, verify each entry
        for entry in ioc_data:
            assert "artifact" in entry, "Each IoC entry should have an 'artifact' field"
            assert "sources" in entry, "Each IoC entry should have a 'sources' field"
    
    # Test threat intelligence lookup if available
    if "get_threat_intelligence" in [tool.name for tool in tools]:
        get_threat_intel_tool = next(tool for tool in tools if tool.name == "get_threat_intelligence")
        threat_intel_result = await get_threat_intel_tool.execute(
            artifact_value="google.com",
            artifact_type="domain_name"
        )
        threat_intel = threat_intel_result.result
        
        print("Type of returned threat_intel:", type(threat_intel))
        
        if threat_intel:
            assert isinstance(threat_intel, dict), "threat_intel should be a dictionary"
            
            # Check for threat intelligence fields
            intel_fields = ["artifact", "sources", "verdict", "prevalence"]
            present_fields = [field for field in intel_fields if field in threat_intel]
            
            print(f"Threat intelligence contains these fields: {', '.join(present_fields)}")
    
    # Test asset enrichment if available
    if "get_asset_enrichment" in [tool.name for tool in tools]:
        get_asset_enrichment_tool = next(tool for tool in tools if tool.name == "get_asset_enrichment")
        asset_enrichment_result = await get_asset_enrichment_tool.execute(
            asset_identifier="192.168.1.1",
            asset_type="ip"
        )
        asset_enrichment = asset_enrichment_result.result
        
        if asset_enrichment:
            assert isinstance(asset_enrichment, dict), "asset_enrichment should be a dictionary"
            
            # Verify asset enrichment fields
            enrichment_fields = ["asset", "first_seen_time", "last_seen_time", "enrichment"]
            present_enrichment_fields = [field for field in enrichment_fields if field in asset_enrichment]
            
            print(f"Asset enrichment contains these fields: {', '.join(present_enrichment_fields)}")
    
    # Test detection results if available
    if "get_detection_results" in [tool.name for tool in tools]:
        get_detection_results_tool = next(tool for tool in tools if tool.name == "get_detection_results")
        detection_results_result = await get_detection_results_tool.execute(
            time_range="1h",
            rule_types=["YARA_L", "MULTI_EVENT"]
        )
        detection_results = detection_results_result.result
        
        if detection_results:
            assert isinstance(detection_results, list), "detection_results should be a list"
            
            if len(detection_results) > 0:
                first_detection = detection_results[0]
                assert isinstance(first_detection, dict), "Each detection should be a dictionary"
                
                detection_fields = ["id", "type", "detection_time", "rule_name"]
                present_detection_fields = [field for field in detection_fields if field in first_detection]
                
                print(f"Detection results contain these fields: {', '.join(present_detection_fields)}")
    
    # Log the structure for debugging
    print(f"Example IoC data structure: {ioc_data}")

    print(f"Successfully retrieved IoC and threat intelligence data")

    return True