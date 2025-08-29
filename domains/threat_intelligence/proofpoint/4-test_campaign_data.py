# 4-test_campaign_data.py

async def test_campaign_data_retrieval(zerg_state=None):    
    """Test Proofpoint campaign data retrieval using the Campaign API"""
    print("Attempting to authenticate using Proofpoint connector")

    import datetime
    import json

    assert zerg_state, "this test requires valid zerg_state"

    proofpoint_api_host = zerg_state.get("proofpoint_api_host").get("value")
    proofpoint_principal = zerg_state.get("proofpoint_principal").get("value")
    proofpoint_secret = zerg_state.get("proofpoint_secret").get("value")

    from connectors.proofpoint.config import ProofpointConnectorConfig
    from connectors.proofpoint.connector import ProofpointConnector
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

    # PART 1: Test Campaign IDs retrieval
    
    # Create an interval for the last 2
    # This reduces the number of API calls while still being likely to find campaigns
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(days=2)
    
    # Format to ISO8601
    interval = f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    print(f"Using time interval: {interval}")
    
    # Find the get_campaign_ids tool
    get_campaign_ids_tool = next((tool for tool in tools if tool.name == "get_campaign_ids"), None)
    assert get_campaign_ids_tool is not None, "get_campaign_ids tool not found"
    
    # Execute the tool to get campaign IDs
    print("Fetching campaign IDs...")
    campaign_ids_result = await get_campaign_ids_tool.execute(
        interval=interval,
        size=10,  # Request 10 campaigns 
        page=1
    )
    campaign_ids_data = campaign_ids_result.raw_result

    print("Type of returned campaign_ids_data:", type(campaign_ids_data))
    print(f"Response structure: {json.dumps(campaign_ids_data, indent=2)[:500]}...")  # Print part of the structure
    
    # Verify the campaigns data structure
    assert isinstance(campaign_ids_data, dict), "campaign_ids_data should be a dict"
    assert "campaigns" in campaign_ids_data, "Missing 'campaigns' field in response"
    assert isinstance(campaign_ids_data["campaigns"], list), "'campaigns' should be a list"
    
    # Check if we found any campaigns
    if campaign_ids_data["campaigns"]:
        print(f"Found {len(campaign_ids_data['campaigns'])} campaigns in the specified time period")
        
        # Check campaign fields for each campaign
        for i, campaign in enumerate(campaign_ids_data["campaigns"][:3]):  # Check only up to 3 campaigns
            print(f"Campaign {i+1}:")
            assert "id" in campaign, "Campaign missing 'id' field"
            
            # Print all available fields in the campaign object
            for key, value in campaign.items():
                print(f"  {key}: {value}")
        
        # Select the first campaign ID for detail testing
        test_campaign_id = campaign_ids_data["campaigns"][0]["id"]
        print(f"\nSelected campaign ID for detail testing: {test_campaign_id}")
    else:
        print("No campaigns found in the specified time period.")
        print("This is not a test failure - but check if this is empty due to no campaigns or due to an API issue")
        return True
    
    # PART 2: Test Campaign Details retrieval
    
    # Find the get_campaign_details tool
    get_campaign_details_tool = next((tool for tool in tools if tool.name == "get_campaign_details"), None)
    assert get_campaign_details_tool is not None, "get_campaign_details tool not found"
    
    # Execute the tool to get campaign details
    print(f"\nFetching details for campaign ID: {test_campaign_id}")
    campaign_details_result = await get_campaign_details_tool.execute(campaign_id=test_campaign_id)
    campaign_details = campaign_details_result.raw_result

    print("Type of returned campaign_details:", type(campaign_details))
    
    # Print the first part of the raw response for debugging
    print(f"Raw campaign details structure: {json.dumps(campaign_details, indent=2)[:500]}...")
    
    # Verify the campaign details structure
    assert isinstance(campaign_details, dict), "campaign_details should be a dict"
    
    # Check that ID is present - this is the only field we require to be present for sure
    assert "id" in campaign_details, "Campaign details missing 'id' field"
    
    # Validate campaign ID matches requested ID
    assert campaign_details["id"] == test_campaign_id, "Returned campaign ID doesn't match requested ID"
    
    # Print campaign details - only print fields that exist
    print("\nCampaign Details:")
    
    # Print all top-level fields except for nested objects/arrays
    for key, value in campaign_details.items():
        if not isinstance(value, (list, dict)) or not value:  # Skip complex structures or empty arrays
            print(f"{key}: {value}")
    
    # Print information about complex fields if they exist
    complex_fields = ["campaignMembers", "actors", "malware", "techniques", "families"]
    for field in complex_fields:
        if field in campaign_details and campaign_details[field]:
            if isinstance(campaign_details[field], list):
                print(f"\n{field} count: {len(campaign_details[field])}")
                
                # Print details for up to 2 items in each complex field
                for i, item in enumerate(campaign_details[field][:2]):
                    print(f"{field} item {i+1}:")
                    
                    if isinstance(item, dict):
                        # For dictionaries, print key-value pairs
                        for item_key, item_value in list(item.items())[:5]:  # Print up to 5 field-value pairs
                            print(f"  {item_key}: {item_value}")
                    else:
                        # For non-dictionary items (like strings), print them directly
                        print(f"  {item}")
    
    print("\nSuccessfully retrieved and validated campaign data")
    return True