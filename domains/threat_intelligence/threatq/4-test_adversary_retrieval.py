# 4-test_adversary_retrieval.py

async def test_adversary_retrieval(zerg_state=None):
    """Test ThreatQ adversary information retrieval"""
    print("Attempting to authenticate using ThreatQ connector")

    assert zerg_state, "this test requires valid zerg_state"

    threatq_api_host = zerg_state.get("threatq_api_host").get("value")
    threatq_api_path = zerg_state.get("threatq_api_path").get("value")
    threatq_username = zerg_state.get("threatq_username").get("value")
    threatq_password = zerg_state.get("threatq_password").get("value")
    threatq_client_id = zerg_state.get("threatq_client_id").get("value")

    from connectors.threatq.config import ThreatQConnectorConfig
    from connectors.threatq.connector import ThreatQConnector
    from connectors.threatq.target import ThreatQTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ThreatQConnectorConfig(
        api_host=threatq_api_host,
        api_path=threatq_api_path,
        username=threatq_username,
        password=threatq_password,
        client_id=threatq_client_id
    )
    assert isinstance(config, ConnectorConfig), "ThreatQConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ThreatQConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ThreatQConnector should be of type Connector"

    # get query target options
    threatq_query_target_options = await connector.get_query_target_options()
    assert isinstance(threatq_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # set up the target
    target = ThreatQTarget()
    assert isinstance(target, ConnectorTargetInterface), "ThreatQTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Find the get_adversaries tool
    get_adversaries_tool = next((tool for tool in tools if tool.name == "get_adversaries"), None)
    assert get_adversaries_tool is not None, "get_adversaries tool not found"
    
    # First, list all adversaries with pagination parameters
    print("Retrieving list of adversaries...")
    adversaries_result = await get_adversaries_tool.execute(
        limit=10,  # Limit to 10 for testing
        offset=0,
        with_attributes=True,  # Include attributes
        with_sources=True,     # Include sources
        with_indicators=True    # Include related indicators
    )
    adversaries = adversaries_result.result

    print("Type of returned adversaries data:", type(adversaries))
    
    # Verify the adversaries data structure
    assert isinstance(adversaries, list), "adversaries should be a list"
    
    # Check if we found any adversaries
    if len(adversaries) > 0:
        print(f"Found {len(adversaries)} adversaries")
        
        # Check adversary fields for the first adversary
        adversary = adversaries[0]
        print("\nSample Adversary Details:")
        print(f"ID: {adversary.get('id')}")
        print(f"Name: {adversary.get('name')}")
        print(f"Type: {adversary.get('type', 'Not specified')}")
        
        # Check for essential fields
        essential_fields = ["id", "name"]
        for field in essential_fields:
            assert field in adversary, f"Adversary missing essential field: {field}"
        
        # Check for optional metadata fields
        optional_fields = ["description", "score", "status", "created_at", "updated_at"]
        present_fields = [field for field in optional_fields if field in adversary]
        print(f"Present metadata fields: {', '.join(present_fields)}")
        
        for field in present_fields:
            print(f"{field.replace('_', ' ').title()}: {adversary.get(field, 'N/A')}")
        
        # Check for attributes if available
        if "attributes" in adversary and adversary["attributes"]:
            print("\nAttributes:")
            assert isinstance(adversary["attributes"], list), "attributes should be a list"
            for attr in adversary["attributes"]:
                assert "name" in attr, "Attribute missing 'name' field"
                assert "value" in attr, "Attribute missing 'value' field"
                print(f"  {attr['name']}: {attr['value']}")
        
        # Check for sources if available
        if "sources" in adversary and adversary["sources"]:
            print("\nSources:")
            assert isinstance(adversary["sources"], list), "sources should be a list"
            for source in adversary["sources"]:
                assert "name" in source, "Source missing 'name' field"
                print(f"  {source['name']}")
        
        # Check for indicators if available
        if "indicators" in adversary and adversary["indicators"]:
            print("\nRelated Indicators:")
            assert isinstance(adversary["indicators"], list), "indicators should be a list"
            for indicator in adversary["indicators"][:5]:  # Show up to 5 indicators
                assert "value" in indicator, "Indicator missing 'value' field"
                assert "type" in indicator, "Indicator missing 'type' field"
                print(f"  {indicator['type']}: {indicator['value']}")
        
        # Now get a specific adversary by ID for detailed testing
        adversary_id = adversary["id"]
        print(f"\nRetrieving details for adversary ID: {adversary_id}")
        
        # Find the get_adversary_by_id tool
        get_adversary_by_id_tool = next((tool for tool in tools if tool.name == "get_adversary_by_id"), None)
        
        if get_adversary_by_id_tool:
            adversary_detail_result = await get_adversary_by_id_tool.execute(
                adversary_id=adversary_id,
                with_attributes=True,
                with_sources=True,
                with_indicators=True
            )
            adversary_detail = adversary_detail_result.result
            
            # Verify the detailed adversary data structure
            assert isinstance(adversary_detail, dict), "adversary_detail should be a dict"
            assert adversary_detail["id"] == adversary_id, "Returned adversary ID doesn't match requested ID"
            
            print("\nDetailed Adversary Information:")
            print(f"ID: {adversary_detail['id']}")
            print(f"Name: {adversary_detail['name']}")
            
            # Print any additional fields that might be in the detailed view
            additional_fields = ["description", "score", "status", "created_at", "updated_at"]
            for field in additional_fields:
                if field in adversary_detail:
                    print(f"{field.replace('_', ' ').title()}: {adversary_detail[field]}")
                    
            # Check and print detailed relationships if available
            for related_type in ["indicators", "attributes", "sources"]:
                if related_type in adversary_detail and adversary_detail[related_type]:
                    print(f"\nRelated {related_type.capitalize()}:")
                    for item in adversary_detail[related_type][:5]:  # Limit to 5 items for readability
                        if related_type == "indicators":
                            print(f"  {item.get('type', 'Unknown')}: {item.get('value', 'N/A')}")
                        elif related_type == "attributes":
                            print(f"  {item.get('name', 'Unknown')}: {item.get('value', 'N/A')}")
                        elif related_type == "sources":
                            print(f"  {item.get('name', 'Unknown')}")
        else:
            print("get_adversary_by_id tool not found, skipping detailed adversary retrieval test")
    else:
        print("No adversaries found in the ThreatQ instance")

    print("\nSuccessfully completed adversary retrieval test")
    return True