# 4-test_list_projects.py

async def test_list_projects(zerg_state=None):
    """Test JIRA project listing through connector tools"""
    print("Testing JIRA project listing via connector tools")

    assert zerg_state, "this test requires valid zerg_state"

    jira_url = zerg_state.get("jira_url").get("value")
    jira_api_token = zerg_state.get("jira_api_token").get("value")
    jira_email = zerg_state.get("jira_email").get("value")

    from connectors.jira.connector.config import JIRAConnectorConfig
    from connectors.jira.connector.connector import JIRAConnector, get_query_target_options, _get_secrets
    from connectors.jira.connector.tools import JIRAConnectorTools, GetJIRAProjectsInput
    from connectors.jira.connector.target import JIRATarget
    from connectors.jira.connector.secrets import JIRASecrets
    from common.models.secret import StorableSecret

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from pydantic import SecretStr
    
    # Define an encryption key for testing
    encryption_key = "test_encryption_key_32_chars_long"

    # Set up the config with StorableSecret for api_key
    config = JIRAConnectorConfig(
        url=jira_url,
        api_key=StorableSecret.model_validate(
            {"secret": jira_api_token}, 
            context={"encryption_key": encryption_key}
        ),
        email=jira_email
    )
    assert isinstance(config, ConnectorConfig), "JIRAConnectorConfig should be of type ConnectorConfig"

    # The connector is already instantiated
    connector = JIRAConnector
    assert isinstance(connector, Connector), "JIRAConnector should be of type Connector"

    # Get secrets
    secrets = await _get_secrets(
        config=config,
        encryption_key=encryption_key,
        user_token=None
    )
    assert secrets is not None, "Failed to get secrets"
    assert isinstance(secrets, JIRASecrets), "Secrets should be of type JIRASecrets"

    # Get query target options to find available projects
    jira_query_target_options = await get_query_target_options(
        config=config,
        secrets=secrets
    )
    assert isinstance(jira_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # Select projects to target
    project_selector = None
    for selector in jira_query_target_options.selectors:
        if selector.type == 'project_keys':  
            project_selector = selector
            break

    assert project_selector, "failed to retrieve project selector from query target options"

    # Grab the first two projects 
    num_projects = 2
    assert isinstance(project_selector.values, list), "project_selector values must be a list"
    assert len(project_selector.values) >= num_projects, f"Need at least {num_projects} projects available"
    project_keys = project_selector.values[:num_projects]
    print(f"Selecting project keys: {project_keys}")

    assert project_keys, f"failed to retrieve {num_projects} project keys from project selector"

    # Set up the target with project keys
    target = JIRATarget(project_keys=project_keys)
    assert isinstance(target, ConnectorTargetInterface), "JIRATarget should be of type ConnectorTargetInterface"

    # Get tools using the connector's get_tools function
    tools = connector.get_tools(
        config=config,
        target=target,
        secrets=secrets,
        cache=None
    )
    assert isinstance(tools, list), "Tools response is not a list"
    assert len(tools) > 0, "Should have at least one tool"

    # Find the get_jira_projects tool
    jira_get_projects_tool = None
    for tool in tools:
        if tool.name == "get_jira_projects":
            jira_get_projects_tool = tool
            break
    
    assert jira_get_projects_tool is not None, "get_jira_projects tool not found"

    # Execute the tool with proper input
    # The GetJIRAProjectsInput model has no required fields
    projects_input = GetJIRAProjectsInput()
    jira_projects_result = await jira_get_projects_tool.execute_fn(projects_input)
    
    # The result should be a list of projects directly (not wrapped in ToolResult here since execute_fn returns the raw result)
    jira_projects = jira_projects_result

    print("Type of returned jira_projects:", type(jira_projects))
    print(f"len projects: {len(jira_projects)} projects: {str(jira_projects)[:200]}")

    # Verify that jira_projects is a list
    assert isinstance(jira_projects, list), "jira_projects should be a list"
    assert len(jira_projects) > 0, "jira_projects should not be empty"
    assert len(jira_projects) == num_projects, f"jira_projects should have {num_projects} entries (filtered by target)"
    
    # Verify structure of each project object
    for project in jira_projects:
        assert isinstance(project, dict), "Each project should be a dictionary"
        assert "key" in project, "Each project should have a 'key' field"
        assert project["key"] in project_keys, f"Project key {project['key']} is not in the requested project_keys"
        
        # Verify essential JIRA project fields
        # These are common fields in JIRA projects based on JIRA API specification
        assert "id" in project, "Each project should have an 'id' field"
        assert "name" in project, "Each project should have a 'name' field"
        
        # Check for additional descriptive fields (optional in some JIRA instances)
        descriptive_fields = ["description", "projectTypeKey", "url", "self", "lead", "components", "issueTypes"]
        present_fields = [field for field in descriptive_fields if field in project]
        
        if present_fields:
            print(f"Project {project['key']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Ensure this is real data, not hardcoded
        assert project["id"] != "hardcoded", "Project data should be from real JIRA API, not hardcoded"
        assert project["name"] != "Test Project", "Project data should be from real JIRA API, not simulated"
        
        # Log the full structure of the first project
        if project == jira_projects[0]:
            import json
            print(f"Example project structure: {json.dumps(project, indent=2, default=str)[:500]}...")

    print(f"Successfully retrieved and validated {len(jira_projects)} JIRA projects")
    print("Verified that projects are real (not simulated) and properly filtered by target")

    return True