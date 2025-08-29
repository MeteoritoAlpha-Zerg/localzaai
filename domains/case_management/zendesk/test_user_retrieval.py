async def test_user_retrieval(zerg_state=None):
    """Test Zendesk user retrieval"""
    print("Retrieving users using Zendesk connector")

    assert zerg_state, "this test requires valid zerg_state"

    zendesk_subdomain = zerg_state.get("zendesk_subdomain").get("value")
    zendesk_email = zerg_state.get("zendesk_email").get("value")
    zendesk_api_token = zerg_state.get("zendesk_api_token").get("value")

    from connectors.zendesk.config import ZendeskConnectorConfig
    from connectors.zendesk.connector import ZendeskConnector
    from connectors.zendesk.tools import ZendeskConnectorTools
    from connectors.zendesk.target import ZendeskTarget

    config = ZendeskConnectorConfig(
        subdomain=zendesk_subdomain,
        email=zendesk_email,
        api_token=SecretStr(zendesk_api_token)
    )
    connector = ZendeskConnector(config)

    connector_target = ZendeskTarget(config=config)
    
    # Get connector tools
    tools = ZendeskConnectorTools(
        zendesk_config=config, 
        target=ZendeskTarget, 
        connector_display_name="Zendesk"
    )
    
    # Retrieve users
    users = await tools.get_zendesk_users(limit=10)
    
    assert users, "Failed to retrieve users"
    
    print(f"Retrieved {len(users)} Zendesk users")
    
    if users and len(users) > 0:
        # Display information about some users
        for i, user in enumerate(users[:3]):
            print(f"User {i+1}:")
            print(f"  ID: {user.get('id')}")
            print(f"  Name: {user.get('name')}")
            print(f"  Email: {user.get('email')}")
            print(f"  Role: {user.get('role')}")
    
    # Try searching for a specific user by email (using the authenticated user's email)
    try:
        user_search = await tools.search_zendesk_users(query=zendesk_email)
        
        if user_search and len(user_search) > 0:
            found_user = user_search[0]
            print(f"Found user {found_user.get('name')} with email {found_user.get('email')}")
            
    except Exception as e:
        print(f"User search failed: {e}")
    
    return True