# 4-test_list_repositories.py

async def test_list_repositories(zerg_state=None):
    """Test CrowdStrike Humio repository enumeration by way of connector tools"""
    print("Testing CrowdStrike Humio repository listing")

    assert zerg_state, "this test requires valid zerg_state"

    humio_api_token = zerg_state.get("humio_api_token").get("value")
    humio_base_url = zerg_state.get("humio_base_url").get("value")
    humio_organization = zerg_state.get("humio_organization").get("value")

    from connectors.crowdstrike_humio.config import CrowdStrikeHumioConnectorConfig
    from connectors.crowdstrike_humio.connector import CrowdStrikeHumioConnector
    from connectors.crowdstrike_humio.target import CrowdStrikeHumioTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = CrowdStrikeHumioConnectorConfig(
        api_token=humio_api_token,
        base_url=humio_base_url,
        organization=humio_organization
    )
    assert isinstance(config, ConnectorConfig), "CrowdStrikeHumioConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CrowdStrikeHumioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CrowdStrikeHumioConnector should be of type Connector"

    # get query target options
    humio_query_target_options = await connector.get_query_target_options()
    assert isinstance(humio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select repositories to target
    repository_selector = None
    for selector in humio_query_target_options.selectors:
        if selector.type == 'repository_names':  
            repository_selector = selector
            break

    assert repository_selector, "failed to retrieve repository selector from query target options"

    # grab the first two repositories 
    num_repositories = 2
    assert isinstance(repository_selector.values, list), "repository_selector values must be a list"
    repository_names = repository_selector.values[:num_repositories] if repository_selector.values else None
    print(f"Selecting repository names: {repository_names}")

    assert repository_names, f"failed to retrieve {num_repositories} repository names from repository selector"

    # set up the target with repository names
    target = CrowdStrikeHumioTarget(repository_names=repository_names)
    assert isinstance(target, ConnectorTargetInterface), "CrowdStrikeHumioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_humio_repositories tool
    humio_get_repositories_tool = next(tool for tool in tools if tool.name == "get_humio_repositories")
    humio_repositories_result = await humio_get_repositories_tool.execute()
    humio_repositories = humio_repositories_result.result

    print("Type of returned humio_repositories:", type(humio_repositories))
    print(f"len repositories: {len(humio_repositories)} repositories: {str(humio_repositories)[:200]}")

    # Verify that humio_repositories is a list
    assert isinstance(humio_repositories, list), "humio_repositories should be a list"
    assert len(humio_repositories) > 0, "humio_repositories should not be empty"
    assert len(humio_repositories) == num_repositories, f"humio_repositories should have {num_repositories} entries"
    
    # Verify structure of each repository object
    for repository in humio_repositories:
        assert "name" in repository, "Each repository should have a 'name' field"
        assert repository["name"] in repository_names, f"Repository name {repository['name']} is not in the requested repository_names"
        
        # Verify essential Humio repository fields
        assert "id" in repository, "Each repository should have an 'id' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["description", "retentionDays", "ingestSizeBasedRetention", "storageSize", "compressedSize"]
        present_fields = [field for field in descriptive_fields if field in repository]
        
        print(f"Repository {repository['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Verify numeric fields are actually numeric if present
        numeric_fields = ["retentionDays", "ingestSizeBasedRetention", "storageSize", "compressedSize"]
        for field in numeric_fields:
            if field in repository and repository[field] is not None:
                assert isinstance(repository[field], (int, float)), f"Field {field} should be numeric"
        
        # Verify retention days is positive if present
        if "retentionDays" in repository and repository["retentionDays"] is not None:
            assert repository["retentionDays"] > 0, "Retention days should be positive"
        
        # Check for data sources if present
        if "dataSources" in repository:
            data_sources = repository["dataSources"]
            assert isinstance(data_sources, list), "Data sources should be a list"
            
            if len(data_sources) > 0:
                sample_ds = data_sources[0]
                ds_fields = ["id", "name", "type"]
                present_ds_fields = [field for field in ds_fields if field in sample_ds]
                print(f"Data sources contain these fields: {', '.join(present_ds_fields)}")
        
        # Log the full structure of the first repository
        if repository == humio_repositories[0]:
            print(f"Example repository structure: {repository}")

    print(f"Successfully retrieved and validated {len(humio_repositories)} CrowdStrike Humio repositories")

    return True