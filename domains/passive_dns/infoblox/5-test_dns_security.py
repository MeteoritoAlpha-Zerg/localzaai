# 5-test_dns_security.py

async def test_dns_security(zerg_state=None):
    """Test Infoblox DNS security data and threat intelligence retrieval"""
    print("Attempting to retrieve DNS security data using Infoblox connector")

    assert zerg_state, "this test requires valid zerg_state"

    infoblox_url = zerg_state.get("infoblox_url").get("value")
    infoblox_username = zerg_state.get("infoblox_username").get("value")
    infoblox_password = zerg_state.get("infoblox_password").get("value")
    infoblox_wapi_version = zerg_state.get("infoblox_wapi_version").get("value")

    from connectors.infoblox.config import InfobloxConnectorConfig
    from connectors.infoblox.connector import InfobloxConnector
    from connectors.infoblox.tools import InfobloxConnectorTools
    from connectors.infoblox.target import InfobloxTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = InfobloxConnectorConfig(
        url=infoblox_url,
        username=infoblox_username,
        password=infoblox_password,
        wapi_version=infoblox_wapi_version,
    )
    assert isinstance(config, ConnectorConfig), "InfobloxConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = InfobloxConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "InfobloxConnector should be of type Connector"

    # get query target options
    infoblox_query_target_options = await connector.get_query_target_options()
    assert isinstance(infoblox_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select networks to target
    network_selector = None
    for selector in infoblox_query_target_options.selectors:
        if selector.type == 'network_refs':  
            network_selector = selector
            break

    assert network_selector, "failed to retrieve network selector from query target options"

    assert isinstance(network_selector.values, list), "network_selector values must be a list"
    network_ref = network_selector.values[0] if network_selector.values else None
    print(f"Selecting network ref: {network_ref}")

    assert network_ref, f"failed to retrieve network ref from network selector"

    # set up the target with network refs
    target = InfobloxTarget(network_refs=[network_ref])
    assert isinstance(target, ConnectorTargetInterface), "InfobloxTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # Test 1: Get DNS security events
    get_infoblox_dns_security_tool = next(tool for tool in tools if tool.name == "get_infoblox_dns_security")
    infoblox_dns_security_result = await get_infoblox_dns_security_tool.execute(
        network_ref=network_ref,
        limit=50  # limit to 50 events for testing
    )
    infoblox_dns_security = infoblox_dns_security_result.result

    print("Type of returned infoblox_dns_security:", type(infoblox_dns_security))
    print(f"len DNS security events: {len(infoblox_dns_security)} events: {str(infoblox_dns_security)[:200]}")

    # Verify that infoblox_dns_security is a list
    assert isinstance(infoblox_dns_security, list), "infoblox_dns_security should be a list"
    
    # DNS security events might be empty, which is acceptable
    if len(infoblox_dns_security) > 0:
        # Limit the number of events to check if there are many
        events_to_check = infoblox_dns_security[:5] if len(infoblox_dns_security) > 5 else infoblox_dns_security
        
        # Verify structure of each DNS security event object
        for event in events_to_check:
            # Verify essential Infoblox DNS security fields
            assert "timestamp" in event, "Each DNS security event should have a 'timestamp' field"
            assert "query_name" in event, "Each DNS security event should have a 'query_name' field"
            assert "event_type" in event, "Each DNS security event should have an 'event_type' field"
            
            # Verify common DNS security fields
            assert "client_ip" in event, "Each DNS security event should have a 'client_ip' field"
            assert "threat_type" in event, "Each DNS security event should have a 'threat_type' field"
            
            # Check for common threat types
            valid_threat_types = ["malware", "phishing", "suspicious", "botnet", "dga", "dns_tunneling", "data_exfiltration"]
            
            # Check for additional optional fields
            optional_fields = ["query_type", "response_code", "blocked", "threat_category", "confidence", "severity"]
            present_optional = [field for field in optional_fields if field in event]
            
            print(f"DNS security event {event['query_name']} ({event['threat_type']}) contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first event for debugging
            if event == events_to_check[0]:
                print(f"Example DNS security event structure: {event}")

        print(f"Successfully retrieved and validated {len(infoblox_dns_security)} Infoblox DNS security events")
    else:
        print("No DNS security events found - this is acceptable for testing")

    # Test 2: Get threat protection policies
    get_infoblox_threat_protection_tool = next(tool for tool in tools if tool.name == "get_infoblox_threat_protection")
    infoblox_threat_protection_result = await get_infoblox_threat_protection_tool.execute()
    infoblox_threat_protection = infoblox_threat_protection_result.result

    print("Type of returned infoblox_threat_protection:", type(infoblox_threat_protection))
    print(f"len threat protection policies: {len(infoblox_threat_protection)} policies: {str(infoblox_threat_protection)[:200]}")

    # Verify that infoblox_threat_protection is a list
    assert isinstance(infoblox_threat_protection, list), "infoblox_threat_protection should be a list"
    
    # Threat protection policies might be empty, which is acceptable
    if len(infoblox_threat_protection) > 0:
        # Limit the number of policies to check
        policies_to_check = infoblox_threat_protection[:3] if len(infoblox_threat_protection) > 3 else infoblox_threat_protection
        
        # Verify structure of each threat protection policy object
        for policy in policies_to_check:
            # Verify essential Infoblox threat protection fields
            assert "_ref" in policy, "Each threat protection policy should have a '_ref' field"
            assert "name" in policy, "Each threat protection policy should have a 'name' field"
            
            # Verify common threat protection fields
            assert "policy_type" in policy, "Each threat protection policy should have a 'policy_type' field"
            
            # Check for common policy types
            valid_policy_types = ["atp", "dns_malware_protection", "dns_data_exfiltration_protection", "lookalike_domain_protection"]
            
            # Check for additional optional fields
            optional_fields = ["enabled", "description", "confidence_threshold", "severity_threshold", "action"]
            present_optional = [field for field in optional_fields if field in policy]
            
            print(f"Threat protection policy {policy['name']} ({policy['policy_type']}) contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first policy for debugging
            if policy == policies_to_check[0]:
                print(f"Example threat protection policy structure: {policy}")

        print(f"Successfully retrieved and validated {len(infoblox_threat_protection)} Infoblox threat protection policies")
    else:
        print("No threat protection policies found - this is acceptable for testing")

    # Test 3: Get DNS analytics data
    get_infoblox_dns_analytics_tool = next(tool for tool in tools if tool.name == "get_infoblox_dns_analytics")
    infoblox_dns_analytics_result = await get_infoblox_dns_analytics_tool.execute(
        network_ref=network_ref,
        limit=30  # limit to 30 analytics records for testing
    )
    infoblox_dns_analytics = infoblox_dns_analytics_result.result

    print("Type of returned infoblox_dns_analytics:", type(infoblox_dns_analytics))
    print(f"len DNS analytics records: {len(infoblox_dns_analytics)} records: {str(infoblox_dns_analytics)[:200]}")

    # Verify that infoblox_dns_analytics is a list
    assert isinstance(infoblox_dns_analytics, list), "infoblox_dns_analytics should be a list"
    
    # DNS analytics might be empty, which is acceptable
    if len(infoblox_dns_analytics) > 0:
        # Check structure of DNS analytics records
        analytics_to_check = infoblox_dns_analytics[:3] if len(infoblox_dns_analytics) > 3 else infoblox_dns_analytics
        
        for analytics in analytics_to_check:
            assert "timestamp" in analytics, "Each DNS analytics record should have a 'timestamp' field"
            assert "query_name" in analytics, "Each DNS analytics record should have a 'query_name' field"
            assert "query_count" in analytics, "Each DNS analytics record should have a 'query_count' field"
            
            # Check for additional analytics fields
            analytics_fields = ["client_ip", "query_type", "response_code", "response_time", "data_size"]
            present_analytics_fields = [field for field in analytics_fields if field in analytics]
            
            print(f"DNS analytics for {analytics['query_name']} contains these fields: {', '.join(present_analytics_fields)}")

        print(f"Successfully retrieved and validated {len(infoblox_dns_analytics)} Infoblox DNS analytics records")
    else:
        print("No DNS analytics records found - this is acceptable for testing")

    print("Successfully completed DNS security and threat intelligence tests")

    return True