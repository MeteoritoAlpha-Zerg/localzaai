# 5-test_threat_summary.py

import datetime
from datetime import timedelta

async def test_threat_summary_retrieval(zerg_state=None):
    """Test Proofpoint threat summary retrieval using the Threats API"""
    print("Attempting to authenticate using Proofpoint connector")

    assert zerg_state, "this test requires valid zerg_state"

    proofpoint_api_host = zerg_state.get("proofpoint_api_host").get("value")
    proofpoint_principal = zerg_state.get("proofpoint_principal").get("value")
    proofpoint_secret = zerg_state.get("proofpoint_secret").get("value")

    from connectors.proofpoint.config import ProofpointConnectorConfig
    from connectors.proofpoint.connector import ProofpointConnector
    from connectors.proofpoint.tools import (
        ProofpointConnectorTools, 
        GetThreatSummaryInput,
        GetCampaignIdsInput,
        GetCampaignDetailsInput
    )
    from connectors.proofpoint.target import ProofpointTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ProofpointConnectorConfig(
        api_host=proofpoint_api_host,
        principal=proofpoint_principal,
        secret=proofpoint_secret
    )
    assert isinstance(config, ConnectorConfig), "ProofpointConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ProofpointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ProofpointConnector should be of type Connector"

    # get query target options
    proofpoint_query_target_options = await connector.get_query_target_options()
    assert isinstance(proofpoint_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # set up the target
    target = ProofpointTarget()
    assert isinstance(target, ConnectorTargetInterface), "ProofpointTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Step 1: First get a campaign ID using the campaign API
    # Create an interval for the last 2 days (to have better chances of finding data)
    end_time = datetime.datetime.utcnow()
    start_time = end_time - timedelta(days=2)
    interval = f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    # Find the get_campaign_ids tool
    get_campaign_ids_tool = next((tool for tool in tools if tool.name == "get_campaign_ids"), None)
    assert get_campaign_ids_tool is not None, "get_campaign_ids tool not found"
    
    # Execute the tool to get campaign IDs
    print(f"Fetching campaign IDs for the last 2 days...")
    campaign_ids_result = await get_campaign_ids_tool.execute(
        interval=interval,
        size=10,
        page=1
    )
    campaign_ids_data = campaign_ids_result.raw_result
    
    # Step 2: Get campaign details to find a threat ID
    test_threat_id = None
    
    if campaign_ids_data.get("campaigns", []):
        # Get the first campaign ID
        campaign_id = campaign_ids_data["campaigns"][0]["id"]
        print(f"Found campaign ID: {campaign_id}")
        
        # Find the get_campaign_details tool
        get_campaign_details_tool = next((tool for tool in tools if tool.name == "get_campaign_details"), None)
        assert get_campaign_details_tool is not None, "get_campaign_details tool not found"
        
        # Execute the tool to get campaign details
        campaign_details_result = await get_campaign_details_tool.execute(campaign_id=campaign_id)
        campaign_details = campaign_details_result.raw_result
        
        # Extract a threat ID from campaign members
        if campaign_details.get("campaignMembers", []):
            test_threat_id = campaign_details["campaignMembers"][0]["id"]
            print(f"Found threat ID from campaign: {test_threat_id}")
    
    # If we still don't have a threat ID, use a fallback (should be a known ID in the environment)
    if not test_threat_id:
        # This should be replaced with a known valid ID for your environment
        test_threat_id = "029bef505d5de699740a1814cba0b6abb685f46d053dea79fd95ba6769e40a6f"
        print(f"Using fallback threat ID: {test_threat_id}")

    # Now perform the actual threat summary test with a valid threat ID
    get_threat_summary_tool = next((tool for tool in tools if tool.name == "get_threat_summary"), None)
    assert get_threat_summary_tool is not None, "get_threat_summary tool not found"
    
    print(f"Getting threat summary for threat ID: {test_threat_id}")
    threat_summary_result = await get_threat_summary_tool.execute(threat_id=test_threat_id)
    threat_summary = threat_summary_result.raw_result

    print("Type of returned threat_summary:", type(threat_summary))
    print(f"Threat summary snippet: {str(threat_summary)[:200]}...")

    # Verify that threat_summary is a dict with the expected structure
    assert isinstance(threat_summary, dict), "threat_summary should be a dict"
    
    # Check essential fields based on the Proofpoint Threats API documentation
    essential_fields = ["id", "name", "type", "category", "status", "severity"]
    for field in essential_fields:
        assert field in threat_summary, f"Threat summary missing essential field: {field}"
    
    # Verify data types based on the API documentation
    assert isinstance(threat_summary["id"], str), "id should be a string"
    assert isinstance(threat_summary["severity"], int), "severity should be an integer"
    
    # Check for array fields
    array_fields = ["actors", "families", "malware", "techniques", "brands"]
    for field in array_fields:
        if field in threat_summary:
            assert isinstance(threat_summary[field], list), f"{field} should be an array/list"
    
    # Check threat type validity
    valid_types = ["attachment", "url", "message text"]
    assert threat_summary["type"] in valid_types, f"type should be one of: {', '.join(valid_types)}"
    
    # Check threat category validity
    valid_categories = ["impostor", "malware", "phish", "spam"]
    assert threat_summary["category"] in valid_categories, f"category should be one of: {', '.join(valid_categories)}"
    
    # Check threat status validity
    valid_statuses = ["active", "cleared"]
    assert threat_summary["status"] in valid_statuses, f"status should be one of: {', '.join(valid_statuses)}"

    # Print details about the threat
    print("\nThreat Details:")
    print(f"Threat ID: {threat_summary['id']}")
    print(f"Threat Name: {threat_summary['name']}")
    print(f"Threat Type: {threat_summary['type']}")
    print(f"Threat Category: {threat_summary['category']}")
    print(f"Threat Severity: {threat_summary['severity']}")
    print(f"Attack Spread: {threat_summary.get('attackSpread', 'N/A')}")
    print(f"Notable: {threat_summary.get('notable', 'N/A')}")
    
    # Print associated entities if available
    for entity_type in ['actors', 'families', 'malware', 'techniques', 'brands']:
        if entity_type in threat_summary and threat_summary[entity_type]:
            print(f"\nAssociated {entity_type.capitalize()}:")
            for entity in threat_summary[entity_type]:
                print(f"  - {entity.get('name', 'Unknown')} (ID: {entity.get('id', 'Unknown')})")

    print(f"\nSuccessfully retrieved and validated threat summary for threat ID: {test_threat_id}")

    return True