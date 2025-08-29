# 6-test_security_analytics.py

async def test_security_analytics(zerg_state=None):
    """Test OpenDNS security analytics and reporting generation"""
    print("Attempting to generate security analytics using OpenDNS connector")

    assert zerg_state, "this test requires valid zerg_state"

    opendns_api_key = zerg_state.get("opendns_api_key").get("value")
    opendns_api_secret = zerg_state.get("opendns_api_secret").get("value")
    opendns_organization_id = zerg_state.get("opendns_organization_id").get("value")

    from connectors.opendns.config import OpenDNSConnectorConfig
    from connectors.opendns.connector import OpenDNSConnector
    from connectors.opendns.tools import OpenDNSConnectorTools, GenerateSecurityAnalyticsInput
    from connectors.opendns.target import OpenDNSTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = OpenDNSConnectorConfig(
        api_key=opendns_api_key,
        api_secret=opendns_api_secret,
        organization_id=opendns_organization_id
    )
    assert isinstance(config, ConnectorConfig), "OpenDNSConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = OpenDNSConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "OpenDNSConnector should be of type Connector"

    # get query target options for organizations
    opendns_query_target_options = await connector.get_query_target_options()
    assert isinstance(opendns_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select organizations to target
    org_selector = None
    for selector in opendns_query_target_options.selectors:
        if selector.type == 'organization_ids':  
            org_selector = selector
            break

    assert org_selector, "failed to retrieve organization selector from query target options"

    assert isinstance(org_selector.values, list), "org_selector values must be a list"
    org_id = org_selector.values[0] if org_selector.values else None
    print(f"Selecting organization ID: {org_id}")

    assert org_id, f"failed to retrieve organization ID from organization selector"

    # set up the target with organization ID
    target = OpenDNSTarget(organization_ids=[org_id])
    assert isinstance(target, ConnectorTargetInterface), "OpenDNSTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the generate_security_analytics tool
    generate_security_analytics_tool = next(tool for tool in tools if tool.name == "generate_security_analytics")
    
    # Test security analytics generation
    security_analytics_result = await generate_security_analytics_tool.execute(
        organization_id=org_id,
        time_period="24h",
        include_trends=True
    )
    security_analytics = security_analytics_result.result

    print("Type of returned security analytics:", type(security_analytics))
    print(f"Security analytics data: {str(security_analytics)[:300]}")

    # Verify that security_analytics is a dictionary with expected structure
    assert isinstance(security_analytics, dict), "security_analytics should be a dictionary"
    
    # Verify essential security analytics fields
    assert "total_requests" in security_analytics, "Security analytics should have a 'total_requests' field"
    assert "blocked_requests" in security_analytics, "Security analytics should have a 'blocked_requests' field"
    assert "threat_summary" in security_analytics, "Security analytics should have a 'threat_summary' field"
    
    # Verify threat summary structure
    threat_summary = security_analytics["threat_summary"]
    assert isinstance(threat_summary, dict), "threat_summary should be a dictionary"
    
    # Check for threat categories
    threat_categories = ["malware", "phishing", "botnets", "command_and_control"]
    present_categories = [cat for cat in threat_categories if cat in threat_summary]
    
    print(f"Threat summary contains these categories: {', '.join(present_categories)}")
    
    # Verify DNS analytics if present
    if "dns_analytics" in security_analytics:
        dns_analytics = security_analytics["dns_analytics"]
        assert isinstance(dns_analytics, dict), "dns_analytics should be a dictionary"
        
        dns_fields = ["query_volume", "unique_domains", "top_domains", "blocked_domains"]
        present_dns_fields = [field for field in dns_fields if field in dns_analytics]
        
        print(f"DNS analytics contains these fields: {', '.join(present_dns_fields)}")
    
    # Verify policy analytics if present
    if "policy_analytics" in security_analytics:
        policy_analytics = security_analytics["policy_analytics"]
        assert isinstance(policy_analytics, dict), "policy_analytics should be a dictionary"
        
        policy_fields = ["policies_triggered", "top_blocked_categories", "policy_effectiveness"]
        present_policy_fields = [field for field in policy_fields if field in policy_analytics]
        
        print(f"Policy analytics contains these fields: {', '.join(present_policy_fields)}")
    
    # Test traffic analytics if available
    if "get_traffic_analytics" in [tool.name for tool in tools]:
        get_traffic_analytics_tool = next(tool for tool in tools if tool.name == "get_traffic_analytics")
        traffic_analytics_result = await get_traffic_analytics_tool.execute(
            organization_id=org_id,
            time_period="1h"
        )
        traffic_analytics = traffic_analytics_result.result
        
        if traffic_analytics:
            assert isinstance(traffic_analytics, dict), "traffic_analytics should be a dictionary"
            
            traffic_fields = ["total_volume", "peak_volume", "unique_clients", "geographic_distribution"]
            present_traffic_fields = [field for field in traffic_fields if field in traffic_analytics]
            
            print(f"Traffic analytics contains these fields: {', '.join(present_traffic_fields)}")
    
    # Test security reporting if available
    if "generate_security_report" in [tool.name for tool in tools]:
        generate_security_report_tool = next(tool for tool in tools if tool.name == "generate_security_report")
        security_report_result = await generate_security_report_tool.execute(
            organization_id=org_id,
            report_type="summary",
            time_period="24h"
        )
        security_report = security_report_result.result
        
        if security_report:
            assert isinstance(security_report, dict), "security_report should be a dictionary"
            
            report_fields = ["executive_summary", "threat_landscape", "recommendations", "metrics"]
            present_report_fields = [field for field in report_fields if field in security_report]
            
            print(f"Security report contains these sections: {', '.join(present_report_fields)}")
    
    # Log the structure of the security analytics for debugging
    print(f"Example security analytics structure: {security_analytics}")
    
    # Verify that the total requests is a reasonable number
    total_requests = security_analytics["total_requests"]
    assert isinstance(total_requests, (int, float)), "total_requests should be a number"
    assert total_requests >= 0, "total_requests should be non-negative"
    
    blocked_requests = security_analytics["blocked_requests"]
    assert isinstance(blocked_requests, (int, float)), "blocked_requests should be a number"
    assert blocked_requests >= 0, "blocked_requests should be non-negative"
    assert blocked_requests <= total_requests, "blocked_requests should not exceed total_requests"
    
    print(f"Successfully generated security analytics: {total_requests} total requests, {blocked_requests} blocked")

    return True