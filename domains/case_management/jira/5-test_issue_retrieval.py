# 5-test_issue_retrieval.py

async def test_issue_retrieval(zerg_state=None):
    """Test JIRA issue retrieval for a specific project"""
    print("Testing JIRA issue retrieval via connector tools")

    assert zerg_state, "this test requires valid zerg_state"

    jira_url = zerg_state.get("jira_url").get("value")
    jira_api_token = zerg_state.get("jira_api_token").get("value")
    jira_email = zerg_state.get("jira_email").get("value")

    from connectors.jira.connector.config import JIRAConnectorConfig
    from connectors.jira.connector.connector import JIRAConnector, get_query_target_options, _get_secrets
    from connectors.jira.connector.tools import JIRAConnectorTools, GetJIRAIssuesInput
    from connectors.jira.connector.target import JIRATarget
    from connectors.jira.connector.secrets import JIRASecrets
    from common.models.secret import StorableSecret
    from common.models.tool import ToolResult

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

    # Select a project to target
    project_selector = None
    for selector in jira_query_target_options.selectors:
        if selector.type == 'project_keys':  
            project_selector = selector
            break

    assert project_selector, "failed to retrieve project selector from query target options"

    assert isinstance(project_selector.values, list), "project_selector values must be a list"
    assert len(project_selector.values) > 0, "Need at least one project available"
    project_key = project_selector.values[0]
    print(f"Selecting project key: {project_key}")

    assert project_key, "failed to retrieve project key from project selector"

    # Set up the target with project key
    # Note: Even though we're querying a specific project, the target is used for filtering
    target = JIRATarget(project_keys=[project_key])
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

    # Find the get_jira_issues tool
    get_jira_issues_tool = None
    for tool in tools:
        if tool.name == "get_jira_issues":
            get_jira_issues_tool = tool
            break
    
    assert get_jira_issues_tool is not None, "get_jira_issues tool not found"

    # Execute the tool with proper input
    # The GetJIRAIssuesInput requires a project_key parameter
    issues_input = GetJIRAIssuesInput(project_key=project_key)
    jira_issues_result = await get_jira_issues_tool.execute_fn(issues_input)
    
    # The _get_jira_issues_async method returns a ToolResult
    assert isinstance(jira_issues_result, ToolResult), "Result should be a ToolResult"
    jira_issues = jira_issues_result.result

    print("Type of returned jira_issues:", type(jira_issues))
    print(f"Number of issues: {len(jira_issues)}")
    if jira_issues:
        print(f"Sample issues: {str(jira_issues[:2])[:500]}...")

    # Verify that jira_issues is a list
    assert isinstance(jira_issues, list), "jira_issues should be a list"
    
    # It's possible a project has no issues, so we check if there are issues to validate
    if len(jira_issues) > 0:
        print(f"Found {len(jira_issues)} issues in project {project_key}")
        
        # Limit the number of issues to check if there are many
        issues_to_check = jira_issues[:5] if len(jira_issues) > 5 else jira_issues
        
        # Verify structure of each issue object
        for issue in issues_to_check:
            assert isinstance(issue, dict), "Each issue should be a dictionary"
            
            # Verify essential JIRA issue fields
            assert "key" in issue, "Each issue should have a 'key' field"
            assert "id" in issue, "Each issue should have an 'id' field"
            
            # Check if issue belongs to the requested project
            # JIRA issue keys follow the format PROJECT-NUMBER (e.g., PROJ-123)
            issue_project_key = issue.get("key", "").split("-")[0] if "-" in issue.get("key", "") else None
            assert issue_project_key == project_key, f"Issue {issue['key']} does not belong to project {project_key}"
            
            # Verify common JIRA issue fields
            assert "self" in issue, "Each issue should have a 'self' field (URL)"
            
            # Check for fields object which contains most issue data
            assert "fields" in issue, "Each issue should have a 'fields' object"
            fields = issue["fields"]
            
            # Check for essential fields
            essential_fields = ["summary", "issuetype", "status", "created"]
            for field in essential_fields:
                assert field in fields, f"Issue fields should contain '{field}'"
            
            # Ensure this is real data, not simulated
            assert not issue["key"].startswith("MOCK-"), "Issues should be from real JIRA API, not mocked"
            assert fields.get("summary") != "Test Issue", "Issues should be real, not simulated"
            
            # Additional optional fields to check (if present)
            optional_fields = ["description", "assignee", "reporter", "priority", "labels", "components", "fixVersions"]
            present_optional = [field for field in optional_fields if field in fields]
            
            if present_optional:
                print(f"Issue {issue['key']} contains these optional fields: {', '.join(present_optional)}")
            
            # Log the structure of the first issue for debugging
            if issue == issues_to_check[0]:
                import json
                print(f"Example issue structure (truncated): {json.dumps(issue, indent=2, default=str)[:800]}...")

        print(f"Successfully retrieved and validated {len(jira_issues)} JIRA issues from project {project_key}")
    else:
        print(f"Project {project_key} has no issues (this is valid)")
        # Even with no issues, the response should still be a valid empty list
        assert jira_issues == [], "Empty project should return empty list, not None"

    print("Verified that issues are real (not simulated) and belong to the correct project")

    return True