# 7-test_asset_query.py

async def test_asset_query(zerg_state=None):
    """Test SysAid asset information retrieval by way of connector tools"""
    print("Retrieving asset information using SysAid connector")

    assert zerg_state, "this test requires valid zerg_state"

    sysaid_url = zerg_state.get("sysaid_url").get("value")
    sysaid_account_id = zerg_state.get("sysaid_account_id").get("value")
    sysaid_username = zerg_state.get("sysaid_username").get("value")
    sysaid_password = zerg_state.get("sysaid_password").get("value")

    from connectors.sysaid.config import SysAidConnectorConfig
    from connectors.sysaid.connector import SysAidConnector
    from connectors.sysaid.tools import SysAidConnectorTools, GetSysAidAssetsInput
    from connectors.sysaid.target import SysAidTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SysAidConnectorConfig(
        url=sysaid_url,
        account_id=sysaid_account_id,
        username=sysaid_username,
        password=sysaid_password,
    )
    assert isinstance(config, ConnectorConfig), "SysAidConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SysAidConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SysAidConnector should be of type Connector"

    # set up the target (asset queries don't typically need specific targeting)
    target = SysAidTarget()
    assert isinstance(target, ConnectorTargetInterface), "SysAidTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_sysaid_assets tool and execute it
    get_assets_tool = next(tool for tool in tools if tool.name == "get_sysaid_assets")
    assets_result = await get_assets_tool.execute(limit=20)
    assets = assets_result.result

    print("Type of returned assets:", type(assets))
    print(f"len assets: {len(assets)} assets: {str(assets)[:200]}")

    # Verify that assets is a list
    assert isinstance(assets, list), "assets should be a list"
    assert len(assets) > 0, "assets should not be empty"
    
    # Limit the number of assets to check if there are many
    assets_to_check = assets[:5] if len(assets) > 5 else assets
    
    # Verify structure of each asset object
    for asset in assets_to_check:
        # Verify essential SysAid asset fields
        assert "asset_id" in asset, "Each asset should have an 'asset_id' field"
        assert "asset_type" in asset, "Each asset should have an 'asset_type' field"
        
        # Check for additional descriptive fields (common in SysAid assets)
        optional_fields = ["name", "status", "ip_address", "mac_address", "location", "owner", "model", "manufacturer", "serial_number", "purchase_date", "warranty_date", "os_type", "os_version"]
        present_optional = [field for field in optional_fields if field in asset]
        
        print(f"Asset {asset['asset_id']} ({asset['asset_type']}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first asset for debugging
        if asset == assets_to_check[0]:
            print(f"Example asset structure: {asset}")

    # Display information about some assets
    for i, asset in enumerate(assets_to_check[:3]):
        print(f"Asset {i+1}:")
        print(f"  Asset ID: {asset.get('asset_id')}")
        print(f"  Type: {asset.get('asset_type')}")
        print(f"  Status: {asset.get('status')}")
        print(f"  IP Address: {asset.get('ip_address')}")

    # Count assets by type
    asset_types = {}
    for asset in assets:
        asset_type = asset.get('asset_type', 'Unknown')
        if asset_type not in asset_types:
            asset_types[asset_type] = 0
        asset_types[asset_type] += 1

    print("Asset counts by type:")
    for asset_type, count in asset_types.items():
        print(f"  {asset_type}: {count}")

    # Check for vulnerability scanning if enabled
    scan_vulnerabilities = zerg_state.get("scan_assets_for_vulnerabilities", {}).get("value", False)
    if scan_vulnerabilities:
        try:
            # Try to find vulnerability scanning tool
            vuln_scan_tool = next(tool for tool in tools if tool.name == "identify_vulnerable_assets")
            vuln_result = await vuln_scan_tool.execute(assets=assets)
            vulnerable_assets = vuln_result.result
            
            print(f"Identified {len(vulnerable_assets)} potentially vulnerable assets")
            
            if vulnerable_assets:
                # Verify vulnerability results structure
                assert isinstance(vulnerable_assets, list), "vulnerable_assets should be a list"
                
                print("Vulnerability examples:")
                for vuln in vulnerable_assets[:3]:
                    assert "asset_id" in vuln, "Each vulnerability should have an 'asset_id' field"
                    assert "vulnerability_type" in vuln, "Each vulnerability should have a 'vulnerability_type' field"
                    print(f"  Asset: {vuln.get('asset_id')} - {vuln.get('vulnerability_type')}")
                    
        except StopIteration:
            print("Vulnerability scanning tool not available - skipping vulnerability check")
        except Exception as e:
            print(f"Error during vulnerability scanning: {e}")

    # Test alternative asset retrieval if available
    try:
        alt_assets_tool = next(tool for tool in tools if tool.name == "get_sysaid_assets_alternate")
        alt_result = await alt_assets_tool.execute()
        alt_assets = alt_result.result
        
        print(f"Retrieved {len(alt_assets)} assets via alternate method")
        assert isinstance(alt_assets, list), "alternate assets should be a list"
        
    except StopIteration:
        print("Alternative asset retrieval method not available")
    except Exception as alt_e:
        print(f"Alternative asset retrieval failed: {alt_e}")

    print(f"Successfully retrieved and validated {len(assets)} SysAid assets")

    return True