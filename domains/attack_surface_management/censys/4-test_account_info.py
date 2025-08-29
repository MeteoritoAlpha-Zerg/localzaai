# 4-test_account_info.py

async def test_account_info(zerg_state=None):
    """Test Censys account information retrieval by way of connector tools"""
    print("Attempting to authenticate using Censys connector")

    assert zerg_state, "this test requires valid zerg_state"

    censys_api_id = zerg_state.get("censys_api_id").get("value")
    censys_api_secret = zerg_state.get("censys_api_secret").get("value")
    censys_base_url = zerg_state.get("censys_base_url").get("value")

    from connectors.censys.config import CensysConnectorConfig
    from connectors.censys.connector import CensysConnector
    from connectors.censys.tools import CensysConnectorTools
    from connectors.censys.target import CensysTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = CensysConnectorConfig(
        api_id=censys_api_id,
        api_secret=censys_api_secret,
        base_url=censys_base_url
    )
    assert isinstance(config, ConnectorConfig), "CensysConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CensysConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CensysConnector should be of type Connector"

    # get query target options
    censys_query_target_options = await connector.get_query_target_options()
    assert isinstance(censys_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select search indices to target
    index_selector = None
    for selector in censys_query_target_options.selectors:
        if selector.type == 'search_indices':  
            index_selector = selector
            break

    assert index_selector, "failed to retrieve search index selector from query target options"

    # grab the first available search index (e.g., 'hosts')
    assert isinstance(index_selector.values, list), "index_selector values must be a list"
    selected_indices = index_selector.values[:1] if index_selector.values else None
    print(f"Selecting search indices: {selected_indices}")

    assert selected_indices, "failed to retrieve search indices from index selector"

    # set up the target with search indices
    target = CensysTarget(search_indices=selected_indices)
    assert isinstance(target, ConnectorTargetInterface), "CensysTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_censys_account_info tool
    censys_get_account_tool = next(tool for tool in tools if tool.name == "get_censys_account_info")
    censys_account_result = await censys_get_account_tool.execute()
    censys_account_info = censys_account_result.result

    print("Type of returned censys_account_info:", type(censys_account_info))
    print(f"Account info: {str(censys_account_info)[:200]}")

    # ensure that censys_account_info is a dictionary with account details
    # and the object having the account information and usage details from the censys specification
    # as may be descriptive
    # Verify that censys_account_info is a dictionary
    assert isinstance(censys_account_info, dict), "censys_account_info should be a dictionary"
    assert len(censys_account_info) > 0, "censys_account_info should not be empty"
    
    # Verify essential Censys account fields
    # These are common fields in Censys account API responses
    essential_fields = ["email", "quota"]
    for field in essential_fields:
        assert field in censys_account_info, f"Account info should have a '{field}' field"
    
    # Check for quota-related information
    if "quota" in censys_account_info:
        quota_info = censys_account_info["quota"]
        assert isinstance(quota_info, dict), "Quota info should be a dictionary"
        
        # Common quota fields
        quota_fields = ["allowance", "used", "resets_at"]
        present_quota_fields = [field for field in quota_fields if field in quota_info]
        print(f"Quota info contains these fields: {', '.join(present_quota_fields)}")
    
    # Check for additional descriptive fields (optional in some Censys accounts)
    descriptive_fields = ["login", "first_login", "last_login", "rate_limit", "plan"]
    present_fields = [field for field in descriptive_fields if field in censys_account_info]
    
    print(f"Account info contains these descriptive fields: {', '.join(present_fields)}")
    
    # Log the full structure
    print(f"Example account info structure: {censys_account_info}")

    print("Successfully retrieved and validated Censys account information")

    return True