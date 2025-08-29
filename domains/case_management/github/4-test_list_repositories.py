# 4-test_list_repositories.py

async def test_list_repositories(zerg_state=None):
    """Test GitHub repository enumeration by way of connector tools"""
    print("Attempting to authenticate using GitHub Issues connector")

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

    # grab the get_github_repositories tool and execute it
    get_github_repositories_tool = next(tool for tool in tools if tool.name == "get_github_repositories")
    github_repositories_result = await get_github_repositories_tool.execute()
    github_repositories = github_repositories_result.result

    print("Type of returned github_repositories:", type(github_repositories))
    print(f"len repositories: {len(github_repositories)} repositories: {str(github_repositories)[:200]}")

    # Verify that github_repositories is a list
    assert isinstance(github_repositories, list), "github_repositories should be a list"
    assert len(github_repositories) > 0, "github_repositories should not be empty"
    
    # Limit the number of repositories to check if there are many
    repos_to_check = github_repositories[:5] if len(github_repositories) > 5 else github_repositories
    
    # Verify structure of each repository object
    for repo in repos_to_check:
        # Verify essential GitHub repository fields
        assert "id" in repo, "Each repository should have an 'id' field"
        assert "name" in repo, "Each repository should have a 'name' field"
        assert "full_name" in repo, "Each repository should have a 'full_name' field"
        
        # Check if repository is one of the requested repositories
        assert repo.get("id") == repository_id, f"Repository {repo['name']} does not match the requested repository_id"
        
        # Verify common GitHub repository fields
        assert "html_url" in repo, "Each repository should have an 'html_url' field"
        
        # Check for essential fields
        essential_fields = ["description", "created_at", "updated_at", "open_issues_count"]
        for field in essential_fields:
            assert field in repo, f"Repository should contain '{field}'"
        
        # Additional optional fields to check (if present)
        optional_fields = ["language", "private", "fork", "default_branch", "owner"]
        present_optional = [field for field in optional_fields if field in repo]
        
        print(f"Repository {repo['name']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first repository for debugging
        if repo == repos_to_check[0]:
            print(f"Example repository structure: {repo}")

    print(f"Successfully retrieved and validated {len(github_repositories)} GitHub repositories")

    return True