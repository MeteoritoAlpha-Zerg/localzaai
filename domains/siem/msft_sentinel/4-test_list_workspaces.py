# 4-test_list_workspaces.py

async def test_list_workspaces(zerg_state=None):
    """Test Microsoft Sentinel workspace enumeration by way of connector tools"""
    print("Attempting to authenticate using Microsoft Sentinel connector")

    assert zerg_state, "this test requires valid zerg_state"

    azure_tenant_id = zerg_state.get("azure_tenant_id").get("value")
    client_id = zerg_state.get("client_id").get("value")
    client_secret = zerg_state.get("client_secret").get("value")
    subscription_id = zerg_state.get("subscription_id").get("value")
    resource_group = zerg_state.get("resource_group").get("value")

    from connectors.microsoft_sentinel.config import MicrosoftSentinelConnectorConfig
    from connectors.microsoft_sentinel.connector import MicrosoftSentinelConnector
    from connectors.microsoft_sentinel.tools import MicrosoftSentinelConnectorTools
    from connectors.microsoft_sentinel.target import MicrosoftSentinelTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = MicrosoftSentinelConnectorConfig(
        tenant_id=azure_tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        subscription_id=subscription_id,
        resource_group=resource_group,
    )
    assert isinstance(config, ConnectorConfig), "MicrosoftSentinelConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = MicrosoftSentinelConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MicrosoftSentinelConnector should be of type Connector"

    # get query target options
    sentinel_query_target_options = await connector.get_query_target_options()
    assert isinstance(sentinel_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select workspaces to target
    workspace_selector = None
    for selector in sentinel_query_target_options.selectors:
        if selector.type == 'workspace_names':  
            workspace_selector = selector
            break

    assert workspace_selector, "failed to retrieve workspace selector from query target options"

    # grab the first two workspaces 
    num_workspaces = 2
    assert isinstance(workspace_selector.values, list), "workspace_selector values must be a list"
    workspace_names = workspace_selector.values[:num_workspaces] if workspace_selector.values else None
    print(f"Selecting workspace names: {workspace_names}")

    assert workspace_names, f"failed to retrieve {num_workspaces} workspace names from workspace selector"

    # set up the target with workspace names
    target = MicrosoftSentinelTarget(workspace_names=workspace_names)
    assert isinstance(target, ConnectorTargetInterface), "MicrosoftSentinelTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_microsoft_sentinel_workspaces tool
    sentinel_get_workspaces_tool = next(tool for tool in tools if tool.name == "get_microsoft_sentinel_workspaces")
    sentinel_workspaces_result = await sentinel_get_workspaces_tool.execute()
    sentinel_workspaces = sentinel_workspaces_result.result

    print("Type of returned sentinel_workspaces:", type(sentinel_workspaces))
    print(f"len workspaces: {len(sentinel_workspaces)} workspaces: {str(sentinel_workspaces)[:200]}")

    # ensure that sentinel_workspaces are a list of objects with the key being the workspace name
    # and the object having the workspace description and other relevant information from the microsoft sentinel specification
    # as may be descriptive
    # Verify that sentinel_workspaces is a list
    assert isinstance(sentinel_workspaces, list), "sentinel_workspaces should be a list"
    assert len(sentinel_workspaces) > 0, "sentinel_workspaces should not be empty"
    assert len(sentinel_workspaces) == num_workspaces, f"sentinel_workspaces should have {num_workspaces} entries"
    
    # Verify structure of each workspace object
    for workspace in sentinel_workspaces:
        assert "name" in workspace, "Each workspace should have a 'name' field"
        assert workspace["name"] in workspace_names, f"Workspace name {workspace['name']} is not in the requested workspace_names"
        
        # Verify essential Microsoft Sentinel workspace fields
        # These are common fields in Microsoft Sentinel workspaces based on Azure API specification
        assert "id" in workspace, "Each workspace should have an 'id' field"
        assert "resourceGroup" in workspace, "Each workspace should have a 'resourceGroup' field"
        
        # Check for additional descriptive fields (optional in some Azure instances)
        descriptive_fields = ["location", "sku", "retentionInDays", "workspaceCapping", "publicNetworkAccessForIngestion", "publicNetworkAccessForQuery"]
        present_fields = [field for field in descriptive_fields if field in workspace]
        
        print(f"Workspace {workspace['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first workspace
        if workspace == sentinel_workspaces[0]:
            print(f"Example workspace structure: {workspace}")

    print(f"Successfully retrieved and validated {len(sentinel_workspaces)} Microsoft Sentinel workspaces")

    return True