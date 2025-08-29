# 4-test_list_domains.py

async def test_list_domains(zerg_state=None):
    """Test Devo domain and data table enumeration by way of connector tools"""
    print("Attempting to authenticate using Devo connector")

    assert zerg_state, "this test requires valid zerg_state"

    devo_url = zerg_state.get("devo_url").get("value")
    devo_api_key = zerg_state.get("devo_api_key", {}).get("value")
    devo_api_secret = zerg_state.get("devo_api_secret", {}).get("value")
    devo_oauth_token = zerg_state.get("devo_oauth_token", {}).get("value")
    devo_domain = zerg_state.get("devo_domain").get("value")

    from connectors.devo.config import DevoConnectorConfig
    from connectors.devo.connector import DevoConnector
    from connectors.devo.tools import DevoConnectorTools
    from connectors.devo.target import DevoTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config - prefer OAuth token over API key/secret
    if devo_oauth_token:
        config = DevoConnectorConfig(
            url=devo_url,
            oauth_token=devo_oauth_token,
            default_domain=devo_domain,
        )
    elif devo_api_key and devo_api_secret:
        config = DevoConnectorConfig(
            url=devo_url,
            api_key=devo_api_key,
            api_secret=devo_api_secret,
            default_domain=devo_domain,
        )
    else:
        raise Exception("Either devo_oauth_token or both devo_api_key and devo_api_secret must be provided")

    assert isinstance(config, ConnectorConfig), "DevoConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = DevoConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DevoConnector should be of type Connector"

    # get query target options
    devo_query_target_options = await connector.get_query_target_options()
    assert isinstance(devo_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select domains to target
    domain_selector = None
    for selector in devo_query_target_options.selectors:
        if selector.type == 'domain_names':  
            domain_selector = selector
            break

    assert domain_selector, "failed to retrieve domain selector from query target options"

    # grab the first two domains 
    num_domains = 2
    assert isinstance(domain_selector.values, list), "domain_selector values must be a list"
    domain_names = domain_selector.values[:num_domains] if domain_selector.values else None
    print(f"Selecting domain names: {domain_names}")

    assert domain_names, f"failed to retrieve {num_domains} domain names from domain selector"

    # set up the target with domain names
    target = DevoTarget(domain_names=domain_names)
    assert isinstance(target, ConnectorTargetInterface), "DevoTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_devo_domains tool
    devo_get_domains_tool = next(tool for tool in tools if tool.name == "get_devo_domains")
    devo_domains_result = await devo_get_domains_tool.execute()
    devo_domains = devo_domains_result.result

    print("Type of returned devo_domains:", type(devo_domains))
    print(f"len domains: {len(devo_domains)} domains: {str(devo_domains)[:200]}")

    # Verify that devo_domains is a list
    assert isinstance(devo_domains, list), "devo_domains should be a list"
    assert len(devo_domains) > 0, "devo_domains should not be empty"
    assert len(devo_domains) == num_domains, f"devo_domains should have {num_domains} entries"
    
    # Verify structure of each domain object
    for domain in devo_domains:
        assert "name" in domain, "Each domain should have a 'name' field"
        assert domain["name"] in domain_names, f"Domain name {domain['name']} is not in the requested domain_names"
        
        # Verify essential Devo domain fields
        assert "tables" in domain, "Each domain should have a 'tables' field"
        assert isinstance(domain["tables"], list), "Domain tables should be a list"
        
        # Check for additional descriptive fields
        descriptive_fields = ["description", "data_retention", "size", "created_at", "last_updated", "permissions"]
        present_fields = [field for field in descriptive_fields if field in domain]
        
        print(f"Domain {domain['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first domain
        if domain == devo_domains[0]:
            print(f"Example domain structure: {domain}")

    print(f"Successfully retrieved and validated {len(devo_domains)} Devo domains")

    # Test data tables as well
    get_devo_tables_tool = next(tool for tool in tools if tool.name == "get_devo_tables")
    devo_tables_result = await get_devo_tables_tool.execute(domain_name=domain_names[0])
    devo_tables = devo_tables_result.result

    print("Type of returned devo_tables:", type(devo_tables))
    
    # Verify tables structure
    assert isinstance(devo_tables, list), "devo_tables should be a list"
    
    if len(devo_tables) > 0:
        # Check first few tables
        tables_to_check = devo_tables[:5] if len(devo_tables) > 5 else devo_tables
        
        for table in tables_to_check:
            assert "name" in table, "Each table should have a 'name' field"
            assert "domain" in table, "Each table should have a 'domain' field"
            
            # Verify table belongs to the requested domain
            assert table["domain"] == domain_names[0], f"Table {table['name']} does not belong to domain {domain_names[0]}"
            
            # Check for additional table fields
            table_fields = ["schema", "row_count", "size_bytes", "created_at", "last_ingestion", "data_type"]
            present_table_fields = [field for field in table_fields if field in table]
            
            print(f"Table {table['name']} contains these fields: {', '.join(present_table_fields)}")
        
        print(f"Successfully retrieved and validated {len(devo_tables)} Devo tables")

    return True