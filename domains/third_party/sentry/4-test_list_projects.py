# 4-test_list_projects.py

async def test_list_projects(zerg_state=None):
    """Test Sentry project enumeration by way of connector tools"""
    print("Testing Sentry project listing")

    assert zerg_state, "this test requires valid zerg_state"

    sentry_api_token = zerg_state.get("sentry_api_token").get("value")
    sentry_organization_slug = zerg_state.get("sentry_organization_slug").get("value")
    sentry_base_url = zerg_state.get("sentry_base_url").get("value")

    from connectors.sentry.config import SentryConnectorConfig
    from connectors.sentry.connector import SentryConnector
    from connectors.sentry.target import SentryTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    config = SentryConnectorConfig(
        api_token=sentry_api_token,
        organization_slug=sentry_organization_slug,
        base_url=sentry_base_url
    )
    assert isinstance(config, ConnectorConfig), "SentryConnectorConfig should be of type ConnectorConfig"

    connector = SentryConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SentryConnector should be of type Connector"

    sentry_query_target_options = await connector.get_query_target_options()
    assert isinstance(sentry_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    project_selector = None
    for selector in sentry_query_target_options.selectors:
        if selector.type == 'project_slugs':  
            project_selector = selector
            break

    assert project_selector, "failed to retrieve project selector from query target options"

    num_projects = 2
    assert isinstance(project_selector.values, list), "project_selector values must be a list"
    project_slugs = project_selector.values[:num_projects] if project_selector.values else None
    print(f"Selecting project slugs: {project_slugs}")

    assert project_slugs, f"failed to retrieve {num_projects} project slugs from project selector"

    target = SentryTarget(project_slugs=project_slugs)
    assert isinstance(target, ConnectorTargetInterface), "SentryTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    sentry_get_projects_tool = next(tool for tool in tools if tool.name == "get_sentry_projects")
    sentry_projects_result = await sentry_get_projects_tool.execute()
    sentry_projects = sentry_projects_result.result

    print("Type of returned sentry_projects:", type(sentry_projects))
    print(f"len projects: {len(sentry_projects)} projects: {str(sentry_projects)[:200]}")

    assert isinstance(sentry_projects, list), "sentry_projects should be a list"
    assert len(sentry_projects) > 0, "sentry_projects should not be empty"
    assert len(sentry_projects) == num_projects, f"sentry_projects should have {num_projects} entries"
    
    for project in sentry_projects:
        assert "slug" in project, "Each project should have a 'slug' field"
        assert project["slug"] in project_slugs, f"Project slug {project['slug']} is not in the requested project_slugs"
        assert "name" in project, "Each project should have a 'name' field"
        assert "id" in project, "Each project should have an 'id' field"
        
        descriptive_fields = ["platform", "status", "dateCreated", "team", "teams"]
        present_fields = [field for field in descriptive_fields if field in project]
        
        print(f"Project {project['slug']} contains these descriptive fields: {', '.join(present_fields)}")
        
        if "status" in project:
            valid_statuses = ["active", "disabled", "pending_deletion"]
            assert project["status"] in valid_statuses, f"Project status should be valid"
        
        if "platform" in project:
            platform = project["platform"]
            assert isinstance(platform, str), "Platform should be a string"
        
        if project == sentry_projects[0]:
            print(f"Example project structure: {project}")

    print(f"Successfully retrieved and validated {len(sentry_projects)} Sentry projects")

    return True