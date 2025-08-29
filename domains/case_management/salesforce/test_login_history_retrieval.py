async def test_login_history_retrieval(zerg_state=None):
    """Test Salesforce login history retrieval for security monitoring"""
    print("Retrieving login history using Salesforce connector")

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
    
    # Use the specialized security tool for login history analysis
    login_history = await tools.get_login_history(days=30)
    
    assert login_history, "Failed to retrieve login history data"
    print(f"Retrieved {len(login_history)} login history entries")
    
    # Use the anomaly detection tool to identify suspicious logins
    suspicious_logins = await tools.detect_login_anomalies(login_data=login_history)
    
    print(f"Detected {len(suspicious_logins)} potentially suspicious login attempts")
    if suspicious_logins:
        sample = suspicious_logins[0]
        print(f"Example suspicious login: User {sample.get('username')} from IP {sample.get('sourceIp')} at {sample.get('loginTime')}")
        print(f"Anomaly reason: {sample.get('anomalyReason')}")
    
    return True