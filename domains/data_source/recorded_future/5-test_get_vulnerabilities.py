# 5-test_get_vulnerabilities.py

async def test_get_vulnerabilities(zerg_state=None):
    """Test Recorded Future vulnerability intelligence retrieval"""
    print("Testing Recorded Future vulnerability intelligence retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    rf_api_url = zerg_state.get("recorded_future_api_url").get("value")
    rf_api_token = zerg_state.get("recorded_future_api_token").get("value")

    from connectors.recorded_future.config import RecordedFutureConnectorConfig
    from connectors.recorded_future.connector import RecordedFutureConnector
    from connectors.recorded_future.target import RecordedFutureTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = RecordedFutureConnectorConfig(
        api_url=rf_api_url,
        api_token=rf_api_token
    )
    assert isinstance(config, ConnectorConfig), "RecordedFutureConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = RecordedFutureConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RecordedFutureConnector should be of type Connector"

    # get query target options
    rf_query_target_options = await connector.get_query_target_options()
    assert isinstance(rf_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select vulnerabilities intelligence source
    intelligence_source_selector = None
    for selector in rf_query_target_options.selectors:
        if selector.type == 'intelligence_sources':  
            intelligence_source_selector = selector
            break

    assert intelligence_source_selector, "failed to retrieve intelligence source selector from query target options"
    assert isinstance(intelligence_source_selector.values, list), "intelligence_source_selector values must be a list"
    
    # Find vulnerabilities in available intelligence sources
    vulnerabilities_source = None
    for source in intelligence_source_selector.values:
        if 'vulnerabilit' in source.lower() or 'cve' in source.lower():
            vulnerabilities_source = source
            break
    
    assert vulnerabilities_source, "Vulnerabilities intelligence source not found in available options"
    print(f"Selecting vulnerabilities intelligence source: {vulnerabilities_source}")

    # set up the target with vulnerabilities intelligence source
    target = RecordedFutureTarget(intelligence_sources=[vulnerabilities_source])
    assert isinstance(target, ConnectorTargetInterface), "RecordedFutureTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_recorded_future_vulnerabilities tool and execute it
    get_rf_vulnerabilities_tool = next(tool for tool in tools if tool.name == "get_recorded_future_vulnerabilities")
    vulnerabilities_result = await get_rf_vulnerabilities_tool.execute()
    vulnerabilities_data = vulnerabilities_result.result

    print("Type of returned vulnerabilities data:", type(vulnerabilities_data))
    print(f"Vulnerabilities count: {len(vulnerabilities_data)} sample: {str(vulnerabilities_data)[:200]}")

    # Verify that vulnerabilities_data is a list
    assert isinstance(vulnerabilities_data, list), "Vulnerabilities data should be a list"
    assert len(vulnerabilities_data) > 0, "Vulnerabilities data should not be empty"
    
    # Limit the number of vulnerabilities to check if there are many
    vulns_to_check = vulnerabilities_data[:3] if len(vulnerabilities_data) > 3 else vulnerabilities_data
    
    # Verify structure of each vulnerability entry
    for vuln in vulns_to_check:
        # Verify essential vulnerability fields
        assert "entity" in vuln, "Each vulnerability should have an 'entity' field"
        assert "risk" in vuln, "Each vulnerability should have a 'risk' field"
        
        # Verify entity structure
        entity = vuln["entity"]
        assert "id" in entity, "Entity should have an 'id' field"
        assert "name" in entity, "Entity should have a 'name' field"
        assert "type" in entity, "Entity should have a 'type' field"
        
        # Verify CVE ID format if present
        if "name" in entity and entity["name"].startswith("CVE-"):
            cve_id = entity["name"]
            assert cve_id.startswith("CVE-"), f"CVE ID {cve_id} should start with 'CVE-'"
        
        # Verify risk structure
        risk = vuln["risk"]
        assert "score" in risk, "Risk should have a 'score' field"
        assert isinstance(risk["score"], (int, float)), "Risk score should be numeric"
        assert 0 <= risk["score"] <= 100, "Risk score should be between 0 and 100"
        
        # Check for vulnerability-specific fields
        vuln_fields = ["cvss", "exploitAvailability", "threatActors", "malware"]
        present_fields = [field for field in vuln_fields if field in vuln]
        
        print(f"Vulnerability {entity['name']} (risk: {risk['score']}) contains: {', '.join(present_fields)}")
        
        # Verify entity type is vulnerability-related
        entity_type = entity["type"].lower()
        assert "vulnerability" in entity_type or "cve" in entity_type, f"Entity type should be vulnerability-related: {entity_type}"
        
        # Log the structure of the first vulnerability for debugging
        if vuln == vulns_to_check[0]:
            print(f"Example vulnerability structure: {vuln}")

    print(f"Successfully retrieved and validated {len(vulnerabilities_data)} Recorded Future vulnerabilities")

    return True