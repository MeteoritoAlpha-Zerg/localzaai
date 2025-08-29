async def test_field_history_tracking(zerg_state=None):
    """Test Salesforce field history tracking for sensitive data"""
    print("Tracking field history for sensitive data using Salesforce connector")

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
    
    # Get the objects that contain sensitive fields per configuration
    sensitive_objects = zerg_state.get("sensitive_fields_mapping").get("value")
    
    # Get a list of history records for sensitive fields
    all_field_history = []
    
    for object_name, fields in sensitive_objects.items():
        try:
            # For each sensitive object, retrieve its history
            history_records = await tools.get_field_history(
                object_name=object_name,
                fields=fields,
                days=30
            )
            
            if history_records:
                all_field_history.extend(history_records)
                print(f"Retrieved {len(history_records)} history records for {object_name}.{', '.join(fields)}")
        except Exception as e:
            print(f"Error retrieving history for {object_name}: {e}")
    
    print(f"Retrieved a total of {len(all_field_history)} field history records for sensitive data")
    
    # Check for suspicious patterns in field changes
    suspicious_changes = await tools.analyze_field_changes(field_history=all_field_history)
    
    if suspicious_changes:
        print(f"Detected {len(suspicious_changes)} potentially suspicious field changes")
        sample = suspicious_changes[0]
        print(f"Example: {sample.get('objectName')}.{sample.get('field')} changed by {sample.get('modifiedBy')} at {sample.get('modifiedDate')}")
        print(f"Concern: {sample.get('securityConcern')}")
    
    return True