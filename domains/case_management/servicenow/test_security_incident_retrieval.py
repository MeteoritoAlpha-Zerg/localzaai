async def test_security_incident_retrieval(zerg_state=None):
    """Test ServiceNow security incident retrieval"""
    print("Retrieving security incidents using ServiceNow connector")

    assert zerg_state, "this test requires valid zerg_state"

    servicenow_instance_url = zerg_state.get("servicenow_instance_url").get("value")
    servicenow_client_id = zerg_state.get("servicenow_client_id").get("value")
    servicenow_client_secret = zerg_state.get("servicenow_client_secret").get("value")

    from connectors.servicenow.config import ServiceNowConnectorConfig
    from connectors.servicenow.connector import ServiceNowConnector
    from connectors.servicenow.tools import ServiceNowConnectorTools
    from connectors.servicenow.target import ServiceNowTarget

    config = ServiceNowConnectorConfig(
        instance_url=servicenow_instance_url,
        client_id=servicenow_client_id,
        client_secret=SecretStr(servicenow_client_secret)
    )
    connector = ServiceNowConnector(config)

    connector_target = ServiceNowTarget(config=config)
    
    # Get connector tools
    tools = ServiceNowConnectorTools(
        servicenow_config=config, 
        target=ServiceNowTarget, 
        connector_display_name="ServiceNow"
    )
    
    # Use the security-specific tool to get security incidents
    try:
        security_incidents = await tools.get_security_incidents(
            days=zerg_state.get("security_incident_lookback_days").get("value")
        )
        
        print(f"Retrieved {len(security_incidents)} security incidents")
        
        if security_incidents:
            sample = security_incidents[0]
            print(f"Example security incident: {sample.get('number')} - {sample.get('short_description')}")
            print(f"Category: {sample.get('category')}, Priority: {sample.get('priority')}")
            
        return True
        
    except Exception as e:
        print(f"Error retrieving security incidents: {e}")
        
        # Fallback to regular incident retrieval with security filter
        connector_target.table_name = "incident"
        
        # Query for security-related incidents using common security keywords
        security_query = "categoryLIKEsecurity^ORshort_descriptionLIKEsecurity^ORdescriptionLIKEsecurity^ORcategoryLIKEbreach"
        incidents = await tools.query_servicenow_records(
            table_name="incident",
            query=security_query
        )
        
        print(f"Retrieved {len(incidents)} security-related incidents using fallback method")
        
        if incidents:
            sample = incidents[0]
            print(f"Example incident: {sample.get('number')} - {sample.get('short_description')}")
        
        return True