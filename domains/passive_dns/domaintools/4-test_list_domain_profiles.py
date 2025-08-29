# 4-test_list_domain_profiles.py

async def test_list_domain_profiles(zerg_state=None):
    """Test DomainTools domain profile enumeration by way of connector tools"""
    print("Testing DomainTools domain profile listing")

    assert zerg_state, "this test requires valid zerg_state"

    domaintools_api_username = zerg_state.get("domaintools_api_username").get("value")
    domaintools_api_key = zerg_state.get("domaintools_api_key").get("value")
    domaintools_base_url = zerg_state.get("domaintools_base_url").get("value")

    from connectors.domaintools.config import DomainToolsConnectorConfig
    from connectors.domaintools.connector import DomainToolsConnector
    from connectors.domaintools.target import DomainToolsTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = DomainToolsConnectorConfig(
        api_username=domaintools_api_username,
        api_key=domaintools_api_key,
        base_url=domaintools_base_url
    )
    assert isinstance(config, ConnectorConfig), "DomainToolsConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = DomainToolsConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DomainToolsConnector should be of type Connector"

    # get query target options
    domaintools_query_target_options = await connector.get_query_target_options()
    assert isinstance(domaintools_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select domain lists to target
    domain_list_selector = None
    for selector in domaintools_query_target_options.selectors:
        if selector.type == 'domain_lists':  
            domain_list_selector = selector
            break

    assert domain_list_selector, "failed to retrieve domain list selector from query target options"

    # grab the first two domain lists 
    num_domain_lists = 2
    assert isinstance(domain_list_selector.values, list), "domain_list_selector values must be a list"
    domain_list_ids = domain_list_selector.values[:num_domain_lists] if domain_list_selector.values else None
    print(f"Selecting domain list IDs: {domain_list_ids}")

    assert domain_list_ids, f"failed to retrieve {num_domain_lists} domain list IDs from domain list selector"

    # set up the target with domain list IDs
    target = DomainToolsTarget(domain_lists=domain_list_ids)
    assert isinstance(target, ConnectorTargetInterface), "DomainToolsTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_domain_profiles tool
    domaintools_get_profiles_tool = next(tool for tool in tools if tool.name == "get_domain_profiles")
    domaintools_profiles_result = await domaintools_get_profiles_tool.execute()
    domain_profiles = domaintools_profiles_result.result

    print("Type of returned domain_profiles:", type(domain_profiles))
    print(f"len profiles: {len(domain_profiles)} profiles: {str(domain_profiles)[:200]}")

    # Verify that domain_profiles is a list
    assert isinstance(domain_profiles, list), "domain_profiles should be a list"
    assert len(domain_profiles) > 0, "domain_profiles should not be empty"
    
    # Verify structure of each domain profile object
    for profile in domain_profiles:
        assert isinstance(profile, dict), "Each domain profile should be a dictionary"
        
        # Verify essential domain profile fields
        assert "domain" in profile, "Each domain profile should have a 'domain' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["registrant", "created_date", "updated_date", "expiration_date", "name_servers", "registrar"]
        present_fields = [field for field in descriptive_fields if field in profile]
        
        print(f"Domain profile {profile['domain']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Verify domain name format
        domain_name = profile["domain"]
        assert isinstance(domain_name, str), "Domain name should be a string"
        assert "." in domain_name, "Domain name should contain at least one dot"
        
        # Check for date fields format if present
        date_fields = ["created_date", "updated_date", "expiration_date"]
        for field in date_fields:
            if field in profile and profile[field]:
                # Date could be in various formats, just ensure it's a string or timestamp
                assert isinstance(profile[field], (str, int, float)), f"Date field {field} should be a string or timestamp"
        
        # Check for name servers if present
        if "name_servers" in profile:
            name_servers = profile["name_servers"]
            assert isinstance(name_servers, list), "Name servers should be a list"
        
        # Log the full structure of the first profile
        if profile == domain_profiles[0]:
            print(f"Example domain profile structure: {profile}")

    print(f"Successfully retrieved and validated {len(domain_profiles)} domain profiles")

    return True