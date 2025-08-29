# 4-test_list_workspaces.py

async def test_list_workspaces(zerg_state=None):
    """Test Asana workspace enumeration by way of connector tools"""
    print("Attempting to authenticate using Asana connector")

    assert zerg_state, "this test requires valid zerg_state"

    asana_personal_access_token = zerg_state.get("asana_personal_access_token").get("value")

    from connectors.asana.config import AsanaConnectorConfig
    from connectors.asana.connector import AsanaConnector
    from connectors.asana.tools import AsanaConnectorTools
    from connectors.asana.target import AsanaTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = AsanaConnectorConfig(
        personal_access_token=asana_personal_access_token,
    )
    assert isinstance(config, ConnectorConfig), "AsanaConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = AsanaConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "AsanaConnector should be of type Connector"

    # get query target options
    asana_query_target_options = await connector.get_query_target_options()
    assert isinstance(asana_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select workspaces to target
    workspace_selector = None
    for selector in asana_query_target_options.selectors:
        if selector.type == 'workspace_gids':  
            workspace_selector = selector
            break

    assert workspace_selector, "failed to retrieve workspace selector from query target options"

    # grab the first two workspaces 
    num_workspaces = 2
    assert isinstance(workspace_selector.values, list), "workspace_selector values must be a list"
    workspace_gids = workspace_selector.values[:num_workspaces] if workspace_selector.values else None
    print(f"Selecting workspace gids: {workspace_gids}")

    assert workspace_gids, f"failed to retrieve {num_workspaces} workspace gids from workspace selector"

    # set up the target with workspace gids
    target = AsanaTarget(workspace_gids=workspace_gids)
    assert isinstance(target, ConnectorTargetInterface), "AsanaTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_asana_workspaces tool
    asana_get_workspaces_tool = next(tool for tool in tools if tool.name == "get_asana_workspaces")
    asana_workspaces_result = await asana_get_workspaces_tool.execute()
    asana_workspaces = asana_workspaces_result.result

    print("Type of returned asana_workspaces:", type(asana_workspaces))
    print(f"len workspaces: {len(asana_workspaces)} workspaces: {str(asana_workspaces)[:200]}")

    # ensure that asana_workspaces are a list of objects with the gid being the workspace gid
    # and the object having the workspace description and other relevant information from the asana specification
    # as may be descriptive
    # Verify that asana_workspaces is a list
    assert isinstance(asana_workspaces, list), "asana_workspaces should be a list"
    assert len(asana_workspaces) > 0, "asana_workspaces should not be empty"
    assert len(asana_workspaces) == num_workspaces, f"asana_workspaces should have {num_workspaces} entries"
    
    # Verify structure of each workspace object
    for workspace in asana_workspaces:
        assert "gid" in workspace, "Each workspace should have a 'gid' field"
        assert workspace["gid"] in workspace_gids, f"Workspace gid {workspace['gid']} is not in the requested workspace_gids"
        
        # Verify essential Asana workspace fields
        # These are common fields in Asana workspaces based on Asana API specification
        assert "name" in workspace, "Each workspace should have a 'name' field"
        
        # Check for additional descriptive fields (optional in some Asana instances)
        descriptive_fields = ["resource_type", "is_organization", "email_domains"]
        present_fields = [field for field in descriptive_fields if field in workspace]
        
        print(f"Workspace {workspace['gid']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if workspace == asana_workspaces[0]:
            print(f"Example workspace structure: {workspace}")

    print(f"Successfully retrieved and validated {len(asana_workspaces)} Asana workspaces")

    return True