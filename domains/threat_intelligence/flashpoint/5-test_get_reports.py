# 5-test_get_reports.py

async def test_get_reports(zerg_state=None):
    """Test Flashpoint deep and dark web intelligence reports retrieval"""
    print("Testing Flashpoint deep and dark web intelligence reports retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    flashpoint_api_url = zerg_state.get("flashpoint_api_url").get("value")
    flashpoint_api_key = zerg_state.get("flashpoint_api_key").get("value")

    from connectors.flashpoint.config import FlashpointConnectorConfig
    from connectors.flashpoint.connector import FlashpointConnector
    from connectors.flashpoint.target import FlashpointTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = FlashpointConnectorConfig(
        api_url=flashpoint_api_url,
        api_key=flashpoint_api_key
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

    data_source_selector = None
    for selector in flashpoint_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    reports_source = None
    for source in data_source_selector.values:
        if 'report' in source.lower():
            reports_source = source
            break
    
    assert reports_source, "Reports data source not found in available options"
    print(f"Selecting reports data source: {reports_source}")

    target = FlashpointTarget(data_sources=[reports_source])
    assert isinstance(target, ConnectorTargetInterface), "FlashpointTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_flashpoint_reports_tool = next(tool for tool in tools if tool.name == "get_flashpoint_reports")
    reports_result = await get_flashpoint_reports_tool.execute()
    reports_data = reports_result.result

    print("Type of returned reports data:", type(reports_data))
    print(f"Reports count: {len(reports_data)} sample: {str(reports_data)[:200]}")

    assert isinstance(reports_data, list), "Reports data should be a list"
    assert len(reports_data) > 0, "Reports data should not be empty"
    
    reports_to_check = reports_data[:5] if len(reports_data) > 5 else reports_data
    
    for report in reports_to_check:
        # Verify essential report fields per Flashpoint API specification
        assert "uuid" in report, "Each report should have a 'uuid' field"
        assert "title" in report, "Each report should have a 'title' field"
        assert "created_at" in report, "Each report should have a 'created_at' field"
        assert "report_type" in report, "Each report should have a 'report_type' field"
        
        assert report["uuid"], "Report UUID should not be empty"
        assert report["title"].strip(), "Report title should not be empty"
        assert report["created_at"], "Created at should not be empty"
        assert report["report_type"].strip(), "Report type should not be empty"
        
        report_fields = ["summary", "tags", "sources", "threat_actors", "malware_families", "attack_vectors"]
        present_fields = [field for field in report_fields if field in report]
        
        print(f"Report {report['uuid'][:8]}... (type: {report['report_type']}) contains: {', '.join(present_fields)}")
        
        # If tags are present, validate structure
        if "tags" in report:
            tags = report["tags"]
            assert isinstance(tags, list), "Tags should be a list"
            for tag in tags:
                assert isinstance(tag, str), "Each tag should be a string"
                assert tag.strip(), "Tag should not be empty"
        
        # If threat actors are present, validate structure
        if "threat_actors" in report:
            threat_actors = report["threat_actors"]
            assert isinstance(threat_actors, list), "Threat actors should be a list"
            for actor in threat_actors:
                assert isinstance(actor, str), "Each threat actor should be a string"
                assert actor.strip(), "Threat actor should not be empty"
        
        # If malware families are present, validate structure
        if "malware_families" in report:
            malware_families = report["malware_families"]
            assert isinstance(malware_families, list), "Malware families should be a list"
            for family in malware_families:
                assert isinstance(family, str), "Each malware family should be a string"
                assert family.strip(), "Malware family should not be empty"
        
        # If sources are present, validate structure
        if "sources" in report:
            sources = report["sources"]
            assert isinstance(sources, list), "Sources should be a list"
            for source in sources:
                assert isinstance(source, dict), "Each source should be a dictionary"
                assert "name" in source, "Each source should have a name"
                assert source["name"].strip(), "Source name should not be empty"
        
        # Log the structure of the first report for debugging
        if report == reports_to_check[0]:
            print(f"Example report structure: {report}")

    print(f"Successfully retrieved and validated {len(reports_data)} Flashpoint reports")

    return True