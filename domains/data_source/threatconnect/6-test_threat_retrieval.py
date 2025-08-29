# 6-test_threat_retrieval.py

async def test_threat_retrieval(zerg_state=None):
    """Test ThreatConnect threat and incident retrieval from sources"""
    print("Attempting to retrieve threats and incidents using ThreatConnect connector")

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

    # grab the get_threatconnect_threats tool and execute it with source name
    get_threatconnect_threats_tool = next(tool for tool in tools if tool.name == "get_threatconnect_threats")
    threatconnect_threats_result = await get_threatconnect_threats_tool.execute(
        source_name=source_name,
        limit=20  # limit to 20 threats for testing
    )
    threatconnect_threats = threatconnect_threats_result.result

    print("Type of returned threatconnect_threats:", type(threatconnect_threats))
    print(f"len threats: {len(threatconnect_threats)} threats: {str(threatconnect_threats)[:200]}")

    # Verify that threatconnect_threats is a list
    assert isinstance(threatconnect_threats, list), "threatconnect_threats should be a list"
    assert len(threatconnect_threats) > 0, "threatconnect_threats should not be empty"
    
    # Limit the number of threats to check if there are many
    threats_to_check = threatconnect_threats[:5] if len(threatconnect_threats) > 5 else threatconnect_threats
    
    # Verify structure of each threat object
    for threat in threats_to_check:
        # Verify essential ThreatConnect threat/group fields
        assert "id" in threat, "Each threat should have an 'id' field"
        assert "name" in threat, "Each threat should have a 'name' field"
        assert "type" in threat, "Each threat should have a 'type' field"
        
        # Verify common ThreatConnect threat fields
        assert "ownerName" in threat, "Each threat should have an 'ownerName' field"
        assert "dateAdded" in threat, "Each threat should have a 'dateAdded' field"
        
        # Check that threat belongs to the requested source
        assert threat["ownerName"] == source_name, f"Threat {threat['id']} does not belong to the requested source {source_name}"
        
        # Check for common threat/group types
        valid_types = ["Adversary", "Campaign", "Document", "Email", "Event", "Incident", "Intrusion Set", "Malware", "Signature", "Tactic", "Task", "Threat"]
        assert threat["type"] in valid_types, f"Threat type {threat['type']} is not a recognized ThreatConnect group type"
        
        # Check for additional optional fields
        optional_fields = ["description", "firstSeen", "lastSeen", "status", "eventDate", "webLink"]
        present_optional = [field for field in optional_fields if field in threat]
        
        print(f"Threat {threat['id']} ({threat['type']}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first threat for debugging
        if threat == threats_to_check[0]:
            print(f"Example threat structure: {threat}")

    print(f"Successfully retrieved and validated {len(threatconnect_threats)} ThreatConnect threats")

    return True