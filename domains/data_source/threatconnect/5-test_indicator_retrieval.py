# 5-test_indicator_retrieval.py

async def test_indicator_retrieval(zerg_state=None):
    """Test ThreatConnect indicator retrieval from sources"""
    print("Attempting to retrieve indicators using ThreatConnect connector")

    assert zerg_state, "this test requires valid zerg_state"

    threatconnect_url = zerg_state.get("threatconnect_url").get("value")
    threatconnect_access_id = zerg_state.get("threatconnect_access_id").get("value")
    threatconnect_secret_key = zerg_state.get("threatconnect_secret_key").get("value")
    threatconnect_default_org = zerg_state.get("threatconnect_default_org").get("value")

    from connectors.threatconnect.config import ThreatConnectConnectorConfig
    from connectors.threatconnect.connector import ThreatConnectConnector
    from connectors.threatconnect.tools import ThreatConnectConnectorTools
    from connectors.threatconnect.target import ThreatConnectTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ThreatConnectConnectorConfig(
        url=threatconnect_url,
        access_id=threatconnect_access_id,
        secret_key=threatconnect_secret_key,
        default_org=threatconnect_default_org,
    )
    assert isinstance(config, ConnectorConfig), "ThreatConnectConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ThreatConnectConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ThreatConnectConnector should be of type Connector"

    # get query target options
    threatconnect_query_target_options = await connector.get_query_target_options()
    assert isinstance(threatconnect_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select sources to target
    source_selector = None
    for selector in threatconnect_query_target_options.selectors:
        if selector.type == 'source_names':  
            source_selector = selector
            break

    assert source_selector, "failed to retrieve source selector from query target options"

    assert isinstance(source_selector.values, list), "source_selector values must be a list"
    source_name = source_selector.values[0] if source_selector.values else None
    print(f"Selecting source name: {source_name}")

    assert source_name, f"failed to retrieve source name from source selector"

    # set up the target with source names
    target = ThreatConnectTarget(source_names=[source_name])
    assert isinstance(target, ConnectorTargetInterface), "ThreatConnectTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_threatconnect_indicators tool and execute it with source name
    get_threatconnect_indicators_tool = next(tool for tool in tools if tool.name == "get_threatconnect_indicators")
    threatconnect_indicators_result = await get_threatconnect_indicators_tool.execute(
        source_name=source_name,
        limit=50  # limit to 50 indicators for testing
    )
    threatconnect_indicators = threatconnect_indicators_result.result

    print("Type of returned threatconnect_indicators:", type(threatconnect_indicators))
    print(f"len indicators: {len(threatconnect_indicators)} indicators: {str(threatconnect_indicators)[:200]}")

    # Verify that threatconnect_indicators is a list
    assert isinstance(threatconnect_indicators, list), "threatconnect_indicators should be a list"
    assert len(threatconnect_indicators) > 0, "threatconnect_indicators should not be empty"
    
    # Limit the number of indicators to check if there are many
    indicators_to_check = threatconnect_indicators[:5] if len(threatconnect_indicators) > 5 else threatconnect_indicators
    
    # Verify structure of each indicator object
    for indicator in indicators_to_check:
        # Verify essential ThreatConnect indicator fields
        assert "id" in indicator, "Each indicator should have an 'id' field"
        assert "summary" in indicator, "Each indicator should have a 'summary' field"
        assert "type" in indicator, "Each indicator should have a 'type' field"
        
        # Verify common ThreatConnect indicator fields
        assert "ownerName" in indicator, "Each indicator should have an 'ownerName' field"
        assert "dateAdded" in indicator, "Each indicator should have a 'dateAdded' field"
        
        # Check that indicator belongs to the requested source
        assert indicator["ownerName"] == source_name, f"Indicator {indicator['id']} does not belong to the requested source {source_name}"
        
        # Check for common indicator types
        valid_types = ["Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR", "Mutex", "Registry Key", "User Agent"]
        assert indicator["type"] in valid_types, f"Indicator type {indicator['type']} is not a recognized ThreatConnect indicator type"
        
        # Check for additional optional fields
        optional_fields = ["description", "rating", "confidence", "threatAssessRating", "threatAssessConfidence", "lastModified", "webLink"]
        present_optional = [field for field in optional_fields if field in indicator]
        
        print(f"Indicator {indicator['id']} ({indicator['type']}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first indicator for debugging
        if indicator == indicators_to_check[0]:
            print(f"Example indicator structure: {indicator}")

    print(f"Successfully retrieved and validated {len(threatconnect_indicators)} ThreatConnect indicators")

    return True