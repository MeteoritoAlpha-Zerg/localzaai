# 5-test_get_services.py

async def test_get_services(zerg_state=None):
    """Test RunZero network services retrieval"""
    print("Testing RunZero network services retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    runzero_api_url = zerg_state.get("runzero_api_url").get("value")
    runzero_api_token = zerg_state.get("runzero_api_token").get("value")
    runzero_organization_id = zerg_state.get("runzero_organization_id").get("value")

    from connectors.runzero.config import RunZeroConnectorConfig
    from connectors.runzero.connector import RunZeroConnector
    from connectors.runzero.target import RunZeroTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = RunZeroConnectorConfig(
        api_url=runzero_api_url,
        api_token=runzero_api_token,
        organization_id=runzero_organization_id
    )
    assert isinstance(config, ConnectorConfig), "RunZeroConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = RunZeroConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RunZeroConnector should be of type Connector"

    # get query target options
    runzero_query_target_options = await connector.get_query_target_options()
    assert isinstance(runzero_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select services data source
    data_source_selector = None
    for selector in runzero_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find services in available data sources
    services_source = None
    for source in data_source_selector.values:
        if 'service' in source.lower():
            services_source = source
            break
    
    assert services_source, "Services data source not found in available options"
    print(f"Selecting services data source: {services_source}")

    # set up the target with services data source
    target = RunZeroTarget(data_sources=[services_source])
    assert isinstance(target, ConnectorTargetInterface), "RunZeroTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_runzero_services tool and execute it
    get_runzero_services_tool = next(tool for tool in tools if tool.name == "get_runzero_services")
    services_result = await get_runzero_services_tool.execute()
    services_data = services_result.result

    print("Type of returned services data:", type(services_data))
    print(f"Services count: {len(services_data)} sample: {str(services_data)[:200]}")

    # Verify that services_data is a list
    assert isinstance(services_data, list), "Services data should be a list"
    assert len(services_data) > 0, "Services data should not be empty"
    
    # Limit the number of services to check if there are many
    services_to_check = services_data[:10] if len(services_data) > 10 else services_data
    
    # Verify structure of each service entry
    for service in services_to_check:
        # Verify essential service fields per RunZero API specification
        assert "id" in service, "Each service should have an 'id' field"
        assert "address" in service, "Each service should have an 'address' field"
        assert "port" in service, "Each service should have a 'port' field"
        assert "protocol" in service, "Each service should have a 'protocol' field"
        
        # Verify address format
        address = service["address"]
        assert isinstance(address, str), "Address should be a string"
        # Basic IP validation (IPv4 or IPv6)
        assert ('.' in address and len(address.split('.')) == 4) or ':' in address, f"Invalid IP address format: {address}"
        
        # Verify port is numeric and valid
        port = service["port"]
        assert isinstance(port, int), "Port should be an integer"
        assert 1 <= port <= 65535, f"Port should be between 1 and 65535: {port}"
        
        # Verify protocol is valid
        protocol = service["protocol"]
        assert isinstance(protocol, str), "Protocol should be a string"
        valid_protocols = ["tcp", "udp", "icmp", "sctp"]
        assert protocol.lower() in valid_protocols, f"Invalid protocol: {protocol}"
        
        # Check for additional service fields per RunZero specification
        service_fields = ["transport", "summary", "product", "version", "banner", "screenshot_link", "attributes"]
        present_fields = [field for field in service_fields if field in service]
        
        print(f"Service {service['id']} ({address}:{port}/{protocol}) contains: {', '.join(present_fields)}")
        
        # If summary is present, validate it's not empty
        if "summary" in service:
            summary = service["summary"]
            assert summary and summary.strip(), "Service summary should not be empty"
        
        # If product is present, validate it's not empty
        if "product" in service:
            product = service["product"]
            assert product and product.strip(), "Service product should not be empty"
        
        # If version is present, validate it's not empty
        if "version" in service:
            version = service["version"]
            assert version and version.strip(), "Service version should not be empty"
        
        # If banner is present, validate it's not empty
        if "banner" in service:
            banner = service["banner"]
            assert banner and banner.strip(), "Service banner should not be empty"
        
        # If attributes are present, validate structure
        if "attributes" in service:
            attributes = service["attributes"]
            assert isinstance(attributes, dict), "Attributes should be a dictionary"
        
        # Log the structure of the first service for debugging
        if service == services_to_check[0]:
            print(f"Example service structure: {service}")

    print(f"Successfully retrieved and validated {len(services_data)} RunZero services")

    return True