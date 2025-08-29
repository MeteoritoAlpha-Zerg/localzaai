# 4-test_list_networks.py

async def test_list_networks(zerg_state=None):
    """Test Infoblox network and DNS view enumeration by way of connector tools"""
    print("Attempting to authenticate using Infoblox connector")

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

    # grab the first two networks 
    num_networks = 2
    assert isinstance(network_selector.values, list), "network_selector values must be a list"
    network_refs = network_selector.values[:num_networks] if network_selector.values else None
    print(f"Selecting network refs: {network_refs}")

    assert network_refs, f"failed to retrieve {num_networks} network refs from network selector"

    # set up the target with network refs
    target = InfobloxTarget(network_refs=network_refs)
    assert isinstance(target, ConnectorTargetInterface), "InfobloxTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_infoblox_networks tool
    infoblox_get_networks_tool = next(tool for tool in tools if tool.name == "get_infoblox_networks")
    infoblox_networks_result = await infoblox_get_networks_tool.execute()
    infoblox_networks = infoblox_networks_result.result

    print("Type of returned infoblox_networks:", type(infoblox_networks))
    print(f"len networks: {len(infoblox_networks)} networks: {str(infoblox_networks)[:200]}")

    # Verify that infoblox_networks is a list
    assert isinstance(infoblox_networks, list), "infoblox_networks should be a list"
    assert len(infoblox_networks) > 0, "infoblox_networks should not be empty"
    assert len(infoblox_networks) == num_networks, f"infoblox_networks should have {num_networks} entries"
    
    # Verify structure of each network object
    for network in infoblox_networks:
        assert "_ref" in network, "Each network should have a '_ref' field"
        assert network["_ref"] in network_refs, f"Network ref {network['_ref']} is not in the requested network_refs"
        
        # Verify essential Infoblox network fields
        assert "network" in network, "Each network should have a 'network' field"
        assert "network_view" in network, "Each network should have a 'network_view' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["comment", "dhcp_utilization", "utilization", "extensible_attributes", "options", "usage"]
        present_fields = [field for field in descriptive_fields if field in network]
        
        print(f"Network {network['network']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first network
        if network == infoblox_networks[0]:
            print(f"Example network structure: {network}")

    print(f"Successfully retrieved and validated {len(infoblox_networks)} Infoblox networks")

    # Test DNS views as well
    get_infoblox_dns_views_tool = next(tool for tool in tools if tool.name == "get_infoblox_dns_views")
    infoblox_dns_views_result = await get_infoblox_dns_views_tool.execute()
    infoblox_dns_views = infoblox_dns_views_result.result

    print("Type of returned infoblox_dns_views:", type(infoblox_dns_views))
    
    # Verify DNS views structure
    assert isinstance(infoblox_dns_views, list), "infoblox_dns_views should be a list"
    
    if len(infoblox_dns_views) > 0:
        # Check first few DNS views
        views_to_check = infoblox_dns_views[:3] if len(infoblox_dns_views) > 3 else infoblox_dns_views
        
        for view in views_to_check:
            assert "_ref" in view, "Each DNS view should have a '_ref' field"
            assert "name" in view, "Each DNS view should have a 'name' field"
            
            # Check for additional DNS view fields
            view_fields = ["is_default", "network_view", "comment", "dns_notify_delay"]
            present_view_fields = [field for field in view_fields if field in view]
            
            print(f"DNS view {view['name']} contains these fields: {', '.join(present_view_fields)}")
        
        print(f"Successfully retrieved and validated {len(infoblox_dns_views)} Infoblox DNS views")

    return True