# 6-test_threat_intelligence_search.py

async def test_threat_intelligence_search(zerg_state=None):
    """Test MISP threat intelligence search functionality"""
    print("Attempting to search threat intelligence using MISP connector")

    assert zerg_state, "this test requires valid zerg_state"

    misp_url = zerg_state.get("misp_url").get("value")
    misp_api_key = zerg_state.get("misp_api_key").get("value")

    from connectors.misp.config import MISPConnectorConfig
    from connectors.misp.connector import MISPConnector
    from connectors.misp.tools import MISPConnectorTools, SearchMISPThreatIntelInput
    from connectors.misp.target import MISPTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = MISPConnectorConfig(
        url=misp_url,
        api_key=misp_api_key
    )
    assert isinstance(config, ConnectorConfig), "MISPConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = MISPConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MISPConnector should be of type Connector"

    # get query target options for organizations
    misp_query_target_options = await connector.get_query_target_options()
    assert isinstance(misp_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select organizations to target
    org_selector = None
    for selector in misp_query_target_options.selectors:
        if selector.type == 'organization_ids':  
            org_selector = selector
            break

    assert org_selector, "failed to retrieve organization selector from query target options"

    assert isinstance(org_selector.values, list), "org_selector values must be a list"
    org_id = org_selector.values[0] if org_selector.values else None
    print(f"Selecting organization ID: {org_id}")

    assert org_id, f"failed to retrieve organization ID from organization selector"

    # set up the target with organization ID
    target = MISPTarget(organization_ids=[org_id])
    assert isinstance(target, ConnectorTargetInterface), "MISPTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the search_misp_threat_intel tool
    search_threat_intel_tool = next(tool for tool in tools if tool.name == "search_misp_threat_intel")
    
    # Test search with attribute type filter
    search_result = await search_threat_intel_tool.execute(
        attribute_type="ip-src",
        limit=10
    )
    search_results = search_result.result

    print("Type of returned search results:", type(search_results))
    print(f"len search results: {len(search_results)} results: {str(search_results)[:200]}")

    # Verify that search_results is a list
    assert isinstance(search_results, list), "search_results should be a list"
    
    if len(search_results) > 0:
        # Limit the number of results to check
        results_to_check = search_results[:3] if len(search_results) > 3 else search_results
        
        # Verify structure of each search result
        for result in results_to_check:
            # Results could be events or attributes depending on search type
            assert "id" in result, "Each result should have an 'id' field"
            
            # Check if it's an event or attribute result
            if "info" in result:
                # This is an event result
                assert "uuid" in result, "Event result should have a 'uuid' field"
                assert "date" in result, "Event result should have a 'date' field"
                print(f"Found event result: {result['id']} - {result.get('info', 'No info')}")
            elif "type" in result and "value" in result:
                # This is an attribute result
                assert "category" in result, "Attribute result should have a 'category' field"
                assert "event_id" in result, "Attribute result should have an 'event_id' field"
                print(f"Found attribute result: {result['type']} - {result['value']}")
            
            # Log the structure of the first result for debugging
            if result == results_to_check[0]:
                print(f"Example search result structure: {result}")

        print(f"Successfully executed threat intelligence search with {len(search_results)} results")
    else:
        print("Search returned no results, which is acceptable for testing purposes")

    return True