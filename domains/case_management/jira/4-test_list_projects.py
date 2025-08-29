# 4-test_list_projects.py

async def test_list_projects(zerg_state=None):
    """Test JIRA project enumeration by way of query target options"""
    print("Attempting to authenticate using JIRA connector")

    assert zerg_state, "this test requires valid zerg_state"

    jira_url = zerg_state.get("jira_url").get("value")
    jira_api_token = zerg_state.get("jira_api_token").get("value")
    jira_email = zerg_state.get("jira_email").get("value")

    from connectors.jira.config import JIRAConnectorConfig
    from connectors.jira.connector import JIRAConnector
    from connectors.jira.tools import JIRAConnectorTools
    from connectors.jira.target import JIRATarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = JIRAConnectorConfig(
        url=jira_url,
        api_token=jira_api_token,
        email=jira_email
    )
    assert isinstance(config, ConnectorConfig), "JIRAConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = JIRAConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "JIRAConnectorConfig should be of type ConnectorConfig"

    # get query target options
    jira_query_target_options = await connector.get_query_target_options()
    assert isinstance(jira_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select projects to target
    project_selector = None
    for selector in jira_query_target_options.selectors:
        if selector.type == 'project_keys':  
            project_selector = selector
            break

    assert project_selector, "failed to retrieve project selector from query target options"

    # grab the first two projects 
    num_projects = 2
    assert isinstance(project_selector.values, list), "project_selector values must be a list"
    project_keys = project_selector.values[:num_projects] if project_selector.values else None
    print(f"Selecting project keys: {project_keys}")

    assert project_keys, f"failed to retrieve {num_projects} project keys from project selector"

    # set up the target with project keys
    target = JIRATarget(project_keys=project_keys)
    assert isinstance(target, ConnectorTargetInterface), "JIRATarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the the get_jira_projects tool
    jira_get_projects_tool = next(tool for tool in tools if tool.name == "get_jira_projects")
    jira_projects_result = await jira_get_projects_tool.execute()
    jira_projects = jira_projects_result.result

    print("Type of returned jira_projects:", type(jira_projects))
    print(f"len projects: {len(jira_projects)} projects: {str(jira_projects)[:200]}")

    # ensure that jira_projects are a list of objects with the key being the project key
    # and the object having the project description and other relevant information from the jira specification
    # as may be descriptive
    # Verify that jira_projects is a list
    assert isinstance(jira_projects, list), "jira_projects should be a list"
    assert len(jira_projects) > 0, "jira_projects should not be empty"
    assert len(jira_projects) == num_projects, f"jira_projects should have {num_projects} entries"
    
    # Verify structure of each project object
    for project in jira_projects:
        assert "key" in project, "Each project should have a 'key' field"
        assert project["key"] in project_keys, f"Project key {project['key']} is not in the requested project_keys"
        
        # Verify essential JIRA project fields
        # These are common fields in JIRA projects based on JIRA API specification
        assert "id" in project, "Each project should have an 'id' field"
        assert "name" in project, "Each project should have a 'name' field"
        
        # Check for additional descriptive fields (optional in some JIRA instances)
        descriptive_fields = ["description", "projectTypeKey", "url", "self"]
        present_fields = [field for field in descriptive_fields if field in project]
        
        print(f"Project {project['key']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first
        if project == jira_projects[0]:
            print(f"Example project structure: {project}")

    print(f"Successfully retrieved and validated {len(jira_projects)} JIRA projects")

    return True