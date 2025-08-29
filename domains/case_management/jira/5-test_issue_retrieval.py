# 5-test_issue_retrieval.py

async def test_issue_retrieval(zerg_state=None):
    """Test JIRA project enumeration by way of query target options"""
    print("Attempting to authenticate using JIRA connector")

    assert zerg_state, "this test requires valid zerg_state"

    jira_url = zerg_state.get("jira_url").get("value")
    jira_api_token = zerg_state.get("jira_api_token").get("value")
    jira_email = zerg_state.get("jira_email").get("value")

    from connectors.jira.config import JIRAConnectorConfig
    from connectors.jira.connector import JIRAConnector
    from connectors.jira.tools import JIRAConnectorTools, GetJIRAIssuesInput
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

    assert isinstance(project_selector.values, list), "project_selector values must be a list"
    project_key = project_selector.values[0] if project_selector.values else None
    print(f"Selecting project key: {project_key}")

    assert project_key, f"failed to retrieve project key from project selector"

    # set up the target with project keys
    target = JIRATarget(project_keys=[project_key])
    assert isinstance(target, ConnectorTargetInterface), "JIRATarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the the get_jira_issues tool and execute it with project key
    get_jira_issues_tool = next(tool for tool in tools if tool.name == "get_jira_issues")
    jira_issues_result = await get_jira_issues_tool.execute(project_key=project_key)
    jira_issues = jira_issues_result.result

    print("Type of returned jira_issues:", type(jira_issues))
    print(f"len projects: {len(jira_issues)} issues: {str(jira_issues)[:200]}")

    # Verify that jira_issues is a list
    assert isinstance(jira_issues, list), "jira_issues should be a list"
    assert len(jira_issues) > 0, "jira_issues should not be empty"
    
    # Limit the number of issues to check if there are many
    issues_to_check = jira_issues[:5] if len(jira_issues) > 5 else jira_issues
    
    # Verify structure of each issue object
    for issue in issues_to_check:
        # Verify essential JIRA issue fields
        assert "key" in issue, "Each issue should have a 'key' field"
        assert "id" in issue, "Each issue should have an 'id' field"
        
        # Check if issue belongs to one of the requested projects
        issue_project_key = issue.get("key", "").split("-")[0] if "-" in issue.get("key", "") else None
        assert issue_project_key == project_key, f"Issue {issue['key']} does not belong to the requested project_keys"
        
        # Verify common JIRA issue fields
        assert "self" in issue, "Each issue should have a 'self' field (URL)"
        
        # Check for fields object which contains most issue data
        assert "fields" in issue, "Each issue should have a 'fields' object"
        fields = issue["fields"]
        
        # Check for essential fields
        essential_fields = ["summary", "issuetype", "status", "created"]
        for field in essential_fields:
            assert field in fields, f"Issue fields should contain '{field}'"
        
        # Additional optional fields to check (if present)
        optional_fields = ["description", "assignee", "reporter", "priority", "labels"]
        present_optional = [field for field in optional_fields if field in fields]
        
        print(f"Issue {issue['key']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first issue for debugging
        if issue == issues_to_check[0]:
            print(f"Example issue structure: {issue}")

    print(f"Successfully retrieved and validated {len(jira_issues)} JIRA issues")

    return True
    