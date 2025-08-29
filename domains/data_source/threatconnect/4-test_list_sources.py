# 4-test_list_sources.py

async def test_list_sources(zerg_state=None):
    """Test ThreatConnect source and group enumeration by way of connector tools"""
    print("Attempting to authenticate using ThreatConnect connector")

    assert zerg_state, "this test requires valid zerg_state"

    threatconnect_url = zerg_state.get("threatconnect_url").get("value")
    threatconnect_access_id = zerg_state.get("threatconnect_access_id").get("value")
    threatconnect_secret_key = zerg_state.get("threatconnect_secret_key").get("value")
    threatconnect_default_org = zerg_state.get("threatconnect_default_org").get("value")

    from connectors.threatconnect.config import ThreatConnectConnectorConfig
    from connectors.threatconnect.connector import ThreatConnectConnector
    from connectors.threatconnect.tools import ThreatConnectConnectorTools
    from connectors.threatconnect.target import ThreatConnectTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions
    
    # set up the config
    config = ThreatConnectConnectorConfig(
        url=threatconnect_url,
        access_id=threatconnect_access_id,
        secret_key=threatconnect_secret_key,
        default_org=threatconnect_default_org,
    )
    assert isinstance(config, ConnectorConfig), "ThreatConnectConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ThreatConnectConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ThreatConnectConnector should be of type Connector"

    # get query target options
    threatconnect_query_target_options = await connector.get_query_target_options()
    assert isinstance(threatconnect_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select sources to target
    source_selector = None
    for selector in threatconnect_query_target_options.selectors:
        if selector.type == 'source_names':  
            source_selector = selector
            break

    assert source_selector, "failed to retrieve source selector from query target options"

    # grab the first two sources 
    num_sources = 2
    assert isinstance(source_selector.values, list), "source_selector values must be a list"
    source_names = source_selector.values[:num_sources] if source_selector.values else None
    print(f"Selecting source names: {source_names}")

    assert source_names, f"failed to retrieve {num_sources} source names from source selector"

    # set up the target with source names
    target = ThreatConnectTarget(source_names=source_names)
    assert isinstance(target, ConnectorTargetInterface), "ThreatConnectTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_threatconnect_sources tool
    threatconnect_get_sources_tool = next(tool for tool in tools if tool.name == "get_threatconnect_sources")
    threatconnect_sources_result = await threatconnect_get_sources_tool.execute()
    threatconnect_sources = threatconnect_sources_result.result

    print("Type of returned threatconnect_sources:", type(threatconnect_sources))
    print(f"len sources: {len(threatconnect_sources)} sources: {str(threatconnect_sources)[:200]}")

    # Verify that threatconnect_sources is a list
    assert isinstance(threatconnect_sources, list), "threatconnect_sources should be a list"
    assert len(threatconnect_sources) > 0, "threatconnect_sources should not be empty"
    assert len(threatconnect_sources) == num_sources, f"threatconnect_sources should have {num_sources} entries"
    
    # Verify structure of each source object
    for source in threatconnect_sources:
        assert "name" in source, "Each source should have a 'name' field"
        assert source["name"] in source_names, f"Source name {source['name']} is not in the requested source_names"
        
        # Verify essential ThreatConnect source fields
        assert "id" in source, "Each source should have an 'id' field"
        assert "type" in source, "Each source should have a 'type' field"
        
        # Check for additional descriptive fields
        descriptive_fields = ["description", "ownerName", "dateAdded", "lastModified", "webLink"]
        present_fields = [field for field in descriptive_fields if field in source]
        
        print(f"Source {source['name']} contains these descriptive fields: {', '.join(present_fields)}")
        
        # Log the full structure of the first source
        if source == threatconnect_sources[0]:
            print(f"Example source structure: {source}")

    print(f"Successfully retrieved and validated {len(threatconnect_sources)} ThreatConnect sources")

    return True