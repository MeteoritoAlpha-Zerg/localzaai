# 6-test_indicator_update.py

import uuid
import datetime

async def test_indicator_update(zerg_state=None):
    """Test ThreatQ updating existing indicators in the threat library"""
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

    # Step 1: First create a new indicator that we can then update
    # We need to find the create indicator tool
    create_indicator_tool = next((tool for tool in tools if tool.name == "create_indicator"), None)
    assert create_indicator_tool is not None, "create_indicator tool not found"

    # Generate a unique indicator value for testing
    test_domain = f"test-update-{uuid.uuid4().hex[:8]}.example.com"
    current_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    test_description = f"Test indicator created for update test at {current_time}"
    
    print(f"\nStep 1: Creating a test indicator for update testing: {test_domain}")
    
    # Create a test indicator
    create_result = await create_indicator_tool.execute(
        value=test_domain,
        type="FQDN",
        status="Review",
        score=50,
        description=test_description,
        attributes=[
            {"name": "Test Attribute", "value": "Initial value"}
        ],
        sources=[
            {"name": "Test Source"}
        ],
        tags=["test", "automation"]
    )
    
    # Verify the creation result
    created_indicator = create_result.result
    assert isinstance(created_indicator, dict), "created_indicator should be a dict"
    assert "id" in created_indicator, "Created indicator missing ID field"
    
    indicator_id = created_indicator["id"]
    print(f"Successfully created test indicator with ID: {indicator_id}")
    
    # Step 2: Retrieve the indicator to confirm it was created correctly
    get_indicator_by_id_tool = next((tool for tool in tools if tool.name == "get_indicator_by_id"), None)
    assert get_indicator_by_id_tool is not None, "get_indicator_by_id tool not found"
    
    print(f"\nStep 2: Verifying the created indicator (ID: {indicator_id})...")
    get_result = await get_indicator_by_id_tool.execute(
        indicator_id=indicator_id,
        with_attributes=True,
        with_sources=True,
        with_tags=True
    )
    
    # Verify the retrieval result
    indicator_before_update = get_result.result
    assert isinstance(indicator_before_update, dict), "indicator_before_update should be a dict"
    assert indicator_before_update["id"] == indicator_id, "Retrieved indicator ID doesn't match created ID"
    assert indicator_before_update["value"] == test_domain, "Retrieved indicator value doesn't match created value"
    
    print("Initial indicator state:")
    print(f"  Value: {indicator_before_update['value']}")
    print(f"  Type: {indicator_before_update['type']}")
    print(f"  Status: {indicator_before_update.get('status', 'N/A')}")
    print(f"  Score: {indicator_before_update.get('score', 'N/A')}")
    print(f"  Description: {indicator_before_update.get('description', 'N/A')}")
    
    # Step 3: Update the indicator
    update_indicator_tool = next((tool for tool in tools if tool.name == "update_indicator"), None)
    assert update_indicator_tool is not None, "update_indicator tool not found"
    
    # Define the updates we want to make
    new_status = "Active"
    new_score = 75
    new_description = f"Updated description at {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    new_attribute_value = "Updated value"
    
    print(f"\nStep 3: Updating the indicator (ID: {indicator_id})...")
    update_result = await update_indicator_tool.execute(
        indicator_id=indicator_id,
        status=new_status,
        score=new_score,
        description=new_description,
        attributes=[
            {"name": "Test Attribute", "value": new_attribute_value},
            {"name": "New Attribute", "value": "Added during update"}
        ],
        tags=["test", "automation", "updated"]
    )
    
    # Verify the update result
    updated_indicator = update_result.result
    assert isinstance(updated_indicator, dict), "updated_indicator should be a dict"
    assert updated_indicator["id"] == indicator_id, "Updated indicator ID doesn't match original ID"
    
    # Step 4: Retrieve the indicator again to verify the updates
    print(f"\nStep 4: Verifying the updates to indicator (ID: {indicator_id})...")
    get_updated_result = await get_indicator_by_id_tool.execute(
        indicator_id=indicator_id,
        with_attributes=True,
        with_sources=True,
        with_tags=True
    )
    
    # Verify the retrieval result after update
    indicator_after_update = get_updated_result.result
    assert isinstance(indicator_after_update, dict), "indicator_after_update should be a dict"
    
    # Verify the updates were applied correctly
    assert indicator_after_update["status"] == new_status, f"Status was not updated. Expected: {new_status}, Got: {indicator_after_update.get('status', 'N/A')}"
    assert indicator_after_update["score"] == new_score, f"Score was not updated. Expected: {new_score}, Got: {indicator_after_update.get('score', 'N/A')}"
    assert indicator_after_update["description"] == new_description, f"Description was not updated. Expected: {new_description}, Got: {indicator_after_update.get('description', 'N/A')}"
    
    print("Updated indicator state:")
    print(f"  Value: {indicator_after_update['value']}")
    print(f"  Type: {indicator_after_update['type']}")
    print(f"  Status: {indicator_after_update.get('status', 'N/A')}")
    print(f"  Score: {indicator_after_update.get('score', 'N/A')}")
    print(f"  Description: {indicator_after_update.get('description', 'N/A')}")
    
    # Check attribute updates
    if "attributes" in indicator_after_update and indicator_after_update["attributes"]:
        print("\nUpdated attributes:")
        for attr in indicator_after_update["attributes"]:
            print(f"  {attr['name']}: {attr['value']}")
            
            # Verify specific attribute updates
            if attr['name'] == "Test Attribute":
                assert attr['value'] == new_attribute_value, f"Attribute 'Test Attribute' was not updated. Expected: {new_attribute_value}, Got: {attr['value']}"
                
        # Check if new attribute was added
        new_attr_found = any(attr['name'] == "New Attribute" for attr in indicator_after_update["attributes"])
        assert new_attr_found, "New attribute 'New Attribute' was not added"
    
    # Check tag updates
    if "tags" in indicator_after_update and indicator_after_update["tags"]:
        print("\nUpdated tags:")
        tag_names = [tag['name'] for tag in indicator_after_update["tags"]]
        print(f"  {', '.join(tag_names)}")
        
        # Verify tag updates
        assert "updated" in tag_names, "Tag 'updated' was not added"
    
    print("\nSuccessfully completed indicator update test")
    
    # Optional: Clean up by deleting the test indicator
    # Uncomment if you want to clean up after the test
    """
    delete_indicator_tool = next((tool for tool in tools if tool.name == "delete_indicator"), None)
    if delete_indicator_tool:
        print(f"\nCleaning up: Deleting test indicator (ID: {indicator_id})...")
        delete_result = await delete_indicator_tool.execute(indicator_id=indicator_id)
        print("Test indicator deleted successfully")
    """
    
    return True