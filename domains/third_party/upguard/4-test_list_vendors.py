# 4-test_list_vendors.py

async def test_list_vendors(zerg_state=None):
    """Test UpGuard vendor and domain enumeration by way of connector tools"""
    print("Attempting to authenticate using UpGuard connector")

    assert zerg_state, "this test requires valid zerg_state"

    upguard_url = zerg_state.get("upguard_url").get("value")
    upguard_api_key = zerg_state.get("upguard_api_key").get("value")

    from connectors.upguard.config import UpGuardConnectorConfig
    from connectors.upguard.connector import UpGuardConnector
    from connectors.upguard.tools import UpGuardConnectorTools
    from connectors.upguard.target import UpGuardTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = UpGuardConnectorConfig(
        url=upguard_url,
        api_key=upguard_api_key,
    )
    assert isinstance(config, ConnectorConfig), "UpGuardConnectorConfig should be of type ConnectorConfig"

    connector = UpGuardConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "UpGuardConnector should be of type Connector"

    upguard_query_target_options = await connector.get_query_target_options()
    assert isinstance(upguard_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    vendor_selector = None
    for selector in upguard_query_target_options.selectors:
        if selector.type == 'vendor_ids':  
            vendor_selector = selector
            break

    assert vendor_selector, "failed to retrieve vendor selector from query target options"

    num_vendors = 2
    assert isinstance(vendor_selector.values, list), "vendor_selector values must be a list"
    vendor_ids = vendor_selector.values[:num_vendors] if vendor_selector.values else None
    print(f"Selecting vendor IDs: {vendor_ids}")

    assert vendor_ids, f"failed to retrieve {num_vendors} vendor IDs from vendor selector"

    target = UpGuardTarget(vendor_ids=vendor_ids)
    assert isinstance(target, ConnectorTargetInterface), "UpGuardTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    upguard_get_vendors_tool = next(tool for tool in tools if tool.name == "get_upguard_vendors")
    upguard_vendors_result = await upguard_get_vendors_tool.execute()
    upguard_vendors = upguard_vendors_result.result

    print("Type of returned upguard_vendors:", type(upguard_vendors))
    print(f"len vendors: {len(upguard_vendors)} vendors: {str(upguard_vendors)[:200]}")

    assert isinstance(upguard_vendors, list), "upguard_vendors should be a list"
    assert len(upguard_vendors) > 0, "upguard_vendors should not be empty"
    assert len(upguard_vendors) == num_vendors, f"upguard_vendors should have {num_vendors} entries"
    
    for vendor in upguard_vendors:
        assert "id" in vendor, "Each vendor should have an 'id' field"
        assert vendor["id"] in vendor_ids, f"Vendor ID {vendor['id']} is not in the requested vendor_ids"
        assert "name" in vendor, "Each vendor should have a 'name' field"
        assert "score" in vendor, "Each vendor should have a 'score' field"
        
        # Verify score is within valid range (0-950)
        assert 0 <= vendor["score"] <= 950, f"Vendor score {vendor['score']} is not within valid range 0-950"
        
        descriptive_fields = ["industry", "size", "tier", "primary_hostname", "created_at", "updated_at"]
        present_fields = [field for field in descriptive_fields if field in vendor]
        
        print(f"Vendor {vendor['name']} (score: {vendor['score']}) contains these descriptive fields: {', '.join(present_fields)}")
        
        if vendor == upguard_vendors[0]:
            print(f"Example vendor structure: {vendor}")

    print(f"Successfully retrieved and validated {len(upguard_vendors)} UpGuard vendors")

    # Test domains as well
    get_upguard_domains_tool = next(tool for tool in tools if tool.name == "get_upguard_domains")
    upguard_domains_result = await get_upguard_domains_tool.execute(limit=10)
    upguard_domains = upguard_domains_result.result

    print("Type of returned upguard_domains:", type(upguard_domains))

    assert isinstance(upguard_domains, list), "upguard_domains should be a list"
    
    if len(upguard_domains) > 0:
        domains_to_check = upguard_domains[:3] if len(upguard_domains) > 3 else upguard_domains
        
        for domain in domains_to_check:
            assert "hostname" in domain, "Each domain should have a 'hostname' field"
            assert "score" in domain, "Each domain should have a 'score' field"
            
            # Verify score is within valid range (0-950)
            assert 0 <= domain["score"] <= 950, f"Domain score {domain['score']} is not within valid range 0-950"
            
            domain_fields = ["vendor_id", "vendor_name", "risk_factors", "is_subsidiary", "last_scanned"]
            present_domain_fields = [field for field in domain_fields if field in domain]
            
            print(f"Domain {domain['hostname']} (score: {domain['score']}) contains these fields: {', '.join(present_domain_fields)}")
        
        print(f"Successfully retrieved and validated {len(upguard_domains)} UpGuard domains")

    return True