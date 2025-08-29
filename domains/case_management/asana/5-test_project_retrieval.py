# 5-test_project_retrieval.py

async def test_project_retrieval(zerg_state=None):
    """Test Asana project retrieval by way of connector tools"""
    print("Attempting to authenticate using Asana connector")

    assert zerg_state, "this test requires valid zerg_state"

    asana_personal_access_token = zerg_state.get("asana_personal_access_token").get("value")

    from connectors.asana.config import AsanaConnectorConfig
    from connectors.asana.connector import AsanaConnector
    from connectors.asana.tools import AsanaConnectorTools, GetAsanaProjectsInput
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

    assert isinstance(workspace_selector.values, list), "workspace_selector values must be a list"
    workspace_gid = workspace_selector.values[0] if workspace_selector.values else None
    print(f"Selecting workspace gid: {workspace_gid}")

    assert workspace_gid, f"failed to retrieve workspace gid from workspace selector"

    # set up the target with workspace gid
    target = AsanaTarget(workspace_gids=[workspace_gid])
    assert isinstance(target, ConnectorTargetInterface), "AsanaTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_asana_projects tool and execute it with workspace gid
    get_asana_projects_tool = next(tool for tool in tools if tool.name == "get_asana_projects")
    asana_projects_result = await get_asana_projects_tool.execute(workspace_gid=workspace_gid)
    asana_projects = asana_projects_result.result

    print("Type of returned asana_projects:", type(asana_projects))
    print(f"len projects: {len(asana_projects)} projects: {str(asana_projects)[:200]}")

    # Verify that asana_projects is a list
    assert isinstance(asana_projects, list), "asana_projects should be a list"
    assert len(asana_projects) > 0, "asana_projects should not be empty"
    
    # Limit the number of projects to check if there are many
    projects_to_check = asana_projects[:5] if len(asana_projects) > 5 else asana_projects
    
    # Verify structure of each project object
    for project in projects_to_check:
        # Verify essential Asana project fields
        assert "gid" in project, "Each project should have a 'gid' field"
        assert "name" in project, "Each project should have a 'name' field"
        
        # Verify common Asana project fields
        assert "resource_type" in project, "Each project should have a 'resource_type' field"
        
        # Check for additional descriptive fields (common in Asana projects)
        optional_fields = ["color", "notes", "public", "archived", "current_status", "team", "owner", "created_at", "modified_at"]
        present_optional = [field for field in optional_fields if field in project]
        
        print(f"Project {project['gid']} ({project['name']}) contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first project for debugging
        if project == projects_to_check[0]:
            print(f"Example project structure: {project}")

    print(f"Successfully retrieved and validated {len(asana_projects)} Asana projects for workspace {workspace_gid}")

    return True