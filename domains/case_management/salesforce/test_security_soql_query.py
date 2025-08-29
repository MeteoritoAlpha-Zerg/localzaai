async def test_security_soql_query(zerg_state=None):
    """Test Salesforce SOQL query execution for security analysis"""
    print("Executing security-focused SOQL query using Salesforce connector")

    assert zerg_state, "this test requires valid zerg_state"

    salesforce_username = zerg_state.get("salesforce_username").get("value")
    salesforce_password = zerg_state.get("salesforce_password").get("value")
    salesforce_security_token = zerg_state.get("salesforce_security_token").get("value")
    salesforce_consumer_key = zerg_state.get("salesforce_consumer_key").get("value")
    salesforce_consumer_secret = zerg_state.get("salesforce_consumer_secret").get("value")
    salesforce_domain = zerg_state.get("salesforce_domain").get("value")

    from connectors.salesforce.config import SalesforceConnectorConfig
    from connectors.salesforce.connector import SalesforceConnector
    from connectors.salesforce.tools import SalesforceConnectorTools
    from connectors.salesforce.target import SalesforceTarget

    config = SalesforceConnectorConfig(
        username=salesforce_username,
        password=SecretStr(salesforce_password),
        security_token=SecretStr(salesforce_security_token),
        consumer_key=salesforce_consumer_key,
        consumer_secret=SecretStr(salesforce_consumer_secret),
        domain=salesforce_domain
    )
    connector = SalesforceConnector(config)

    connector_target = SalesforceTarget(config=config)
    
    # Get connector tools
    tools = SalesforceConnectorTools(
        salesforce_config=config, 
        target=SalesforceTarget, 
        connector_display_name="Salesforce"
    )
    
    # Execute a SOQL query to get user login history (a security-relevant dataset)
    # This assumes LoginHistory is accessible to the authenticated user
    login_history_query = """
        SELECT Id, UserId, LoginTime, SourceIp, LoginType, Status, Browser, Platform
        FROM LoginHistory
        ORDER BY LoginTime DESC
        LIMIT 10
    """
    
    try:
        login_results = await tools.execute_soql_query(query=login_history_query)
        print(f"Successfully retrieved {len(login_results)} login history records")
        
        if login_results:
            print(f"Most recent login: {login_results[0]}")
    except Exception as e:
        print(f"Login history query failed: {e}")
        
        # Try a fallback query on User object since LoginHistory might not be accessible
        users_query = """
            SELECT Id, Username, LastLoginDate, Profile.Name, IsActive
            FROM User
            WHERE IsActive = true
            ORDER BY LastLoginDate DESC
            LIMIT 10
        """
        
        user_results = await tools.execute_soql_query(query=users_query)
        print(f"Successfully retrieved {len(user_results)} user records")
        
        if user_results:
            print(f"Sample user data: {user_results[0]}")
    
    return True