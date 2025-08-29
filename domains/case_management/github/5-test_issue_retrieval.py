# 5-test_issue_retrieval.py

async def test_issue_retrieval(zerg_state=None):
    """Test GitHub issue retrieval for a selected repository"""
    print("Attempting to authenticate using GitHub connector")

    assert zerg_state, "this test requires valid zerg_state"

    github_api_url = zerg_state.get("github_api_url").get("value")
    github_access_token = zerg_state.get("github_access_token").get("value")

    from connectors.github.config import GithubConnectorConfig
    from connectors.github.connector import GithubConnector
    from connectors.github.tools import GithubConnectorTools
    from connectors.github.target import GithubTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = GithubConnectorConfig(
        url=github_api_url,
        access_token=github_access_token
    )
    assert isinstance(config, ConnectorConfig), "GithubConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = GithubConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GithubConnector should be of type Connector"

    # get query target options
    github_query_target_options = await connector.get_query_target_options()
    assert isinstance(github_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select repositories to target
    repository_selector = None
    for selector in github_query_target_options.selectors:
        if selector.type == 'repository_ids':  
            repository_selector = selector
            break

    assert repository_selector, "failed to retrieve repository selector from query target options"

    assert isinstance(repository_selector.values, list), "repository_selector values must be a list"
    repository_id = repository_selector.values[0] if repository_selector.values else None
    print(f"Selecting repository id: {repository_id}")

    assert repository_id, f"failed to retrieve repository id from repository selector"

    # set up the target with repository ids
    target = GithubTarget(repository_ids=[repository_id])
    assert isinstance(target, ConnectorTargetInterface), "GithubTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the the get_github_issues tool and execute it with repository id
    get_github_issues_tool = next(tool for tool in tools if tool.name == "get_github_issues")
    github_issues_result = await get_github_issues_tool.execute(repository_id=repository_id)
    github_issues = github_issues_result.result

    print("Type of returned github_issues:", type(github_issues))
    print(f"len issues: {len(github_issues)} issues: {str(github_issues)[:200]}")

    # Verify that github_issues is a list
    assert isinstance(github_issues, list), "github_issues should be a list"
    assert len(github_issues) > 0, "github_issues should not be empty"
    
    # Limit the number of issues to check if there are many
    issues_to_check = github_issues[:5] if len(github_issues) > 5 else github_issues
    
    # Verify structure of each issue object
    for issue in issues_to_check:
        # Verify essential GitHub issue fields
        assert "number" in issue, "Each issue should have a 'number' field"
        assert "id" in issue, "Each issue should have an 'id' field"
        assert "title" in issue, "Each issue should have a 'title' field"
        
        # Check if issue belongs to one of the requested repositories
        assert "repository_url" in issue, "Each issue should have a 'repository_url' field"
        repo_url_parts = issue.get("repository_url", "").split("/")
        repo_name = repo_url_parts[-1] if len(repo_url_parts) > 1 else None
        print(f"Issue #{issue['number']} belongs to repository: {repo_name}")
        
        # Verify common GitHub issue fields
        assert "html_url" in issue, "Each issue should have an 'html_url' field"
        assert "url" in issue, "Each issue should have a 'url' field"
        
        # Check for essential fields
        essential_fields = ["state", "created_at", "updated_at", "body"]
        for field in essential_fields:
            assert field in issue, f"Issue should contain '{field}'"
        
        # Additional optional fields to check (if present)
        optional_fields = ["assignee", "assignees", "labels", "milestone", "comments", "closed_at", "user"]
        present_optional = [field for field in optional_fields if field in issue]
        
        print(f"Issue #{issue['number']} contains these optional fields: {', '.join(present_optional)}")
        
        # Verify issue state
        assert issue["state"] in ["open", "closed"], f"Issue state should be 'open' or 'closed', got '{issue['state']}'"
        
        # Log the structure of the first issue for debugging
        if issue == issues_to_check[0]:
            print(f"Example issue structure: {issue}")

    print(f"Successfully retrieved and validated {len(github_issues)} GitHub issues")

    return True