# 6-test_task_retrieval.py

async def test_task_retrieval(zerg_state=None):
    """Test Asana task retrieval by way of connector tools"""
    print("Attempting to retrieve tasks using Asana connector")

    assert zerg_state, "this test requires valid zerg_state"

    asana_personal_access_token = zerg_state.get("asana_personal_access_token").get("value")

    from connectors.asana.config import AsanaConnectorConfig
    from connectors.asana.connector import AsanaConnector
    from connectors.asana.tools import AsanaConnectorTools, GetAsanaTasksInput
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

    # set up the target with workspace gid to get projects
    target = AsanaTarget(workspace_gids=[workspace_gid])
    assert isinstance(target, ConnectorTargetInterface), "AsanaTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # get projects from this workspace first
    get_asana_projects_tool = next(tool for tool in tools if tool.name == "get_asana_projects")
    asana_projects_result = await get_asana_projects_tool.execute(workspace_gid=workspace_gid)
    asana_projects = asana_projects_result.result

    assert isinstance(asana_projects, list), "asana_projects should be a list"
    assert len(asana_projects) > 0, "asana_projects should not be empty"

    # select the first project
    first_project = asana_projects[0]
    project_gid = first_project.get('gid')
    project_name = first_project.get('name', 'Unknown')
    
    print(f"Using project: {project_gid} - {project_name}")

    # now get tasks from this project
    get_asana_tasks_tool = next(tool for tool in tools if tool.name == "get_asana_tasks")
    asana_tasks_result = await get_asana_tasks_tool.execute(project_gid=project_gid)
    asana_tasks = asana_tasks_result.result

    print("Type of returned asana_tasks:", type(asana_tasks))
    print(f"len tasks: {len(asana_tasks)} tasks: {str(asana_tasks)[:200]}")

    # Verify that asana_tasks is a list
    assert isinstance(asana_tasks, list), "asana_tasks should be a list"
    assert len(asana_tasks) >= 0, "asana_tasks should be a valid list (can be empty)"
    
    if len(asana_tasks) > 0:
        # Limit the number of tasks to check if there are many
        tasks_to_check = asana_tasks[:5] if len(asana_tasks) > 5 else asana_tasks
        
        # Verify structure of each task object
        for task in tasks_to_check:
            # Verify essential Asana task fields
            assert "gid" in task, "Each task should have a 'gid' field"
            assert "name" in task, "Each task should have a 'name' field"
            
            # Verify common Asana task fields
            assert "resource_type" in task, "Each task should have a 'resource_type' field"
            
            # Check for additional descriptive fields (common in Asana tasks)
            optional_fields = ["notes", "completed", "assignee", "due_on", "due_at", "created_at", "modified_at", "completed_at", "tags", "projects", "parent", "subtasks", "dependencies", "dependents", "permalink_url"]
            present_optional = [field for field in optional_fields if field in task]
            
            print(f"Task {task['gid']} ({task['name']}) contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first task for debugging
            if task == tasks_to_check[0]:
                print(f"Example task structure: {task}")

        # Display information about the first task
        first_task = asana_tasks[0]
        task_name = first_task.get('name', 'Unknown')
        task_gid = first_task.get('gid', 'Unknown')
        task_completed = first_task.get('completed', False)
        
        print(f"First task: {task_gid} - {task_name} (Completed: {task_completed})")

        print(f"Successfully retrieved and validated {len(asana_tasks)} Asana tasks from project {project_name}")
    else:
        print(f"Project {project_name} contains no tasks - this is valid")

    return True