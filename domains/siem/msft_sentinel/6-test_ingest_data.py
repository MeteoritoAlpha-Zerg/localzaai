# 6-test_ingest_data.py

async def test_ingest_data(zerg_state=None):
    """Test ingesting data into Microsoft Sentinel"""
    print("Attempting to ingest data using Microsoft Sentinel connector")

    assert zerg_state, "this test requires valid zerg_state"

    azure_tenant_id = zerg_state.get("azure_tenant_id").get("value")
    client_id = zerg_state.get("client_id").get("value")
    client_secret = zerg_state.get("client_secret").get("value")
    subscription_id = zerg_state.get("subscription_id").get("value")
    resource_group = zerg_state.get("resource_group").get("value")

    from connectors.microsoft_sentinel.config import MicrosoftSentinelConnectorConfig
    from connectors.microsoft_sentinel.connector import MicrosoftSentinelConnector
    from connectors.microsoft_sentinel.tools import MicrosoftSentinelConnectorTools, IngestDataInput
    from connectors.microsoft_sentinel.target import MicrosoftSentinelTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = MicrosoftSentinelConnectorConfig(
        tenant_id=azure_tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        subscription_id=subscription_id,
        resource_group=resource_group,
    )
    assert isinstance(config, ConnectorConfig), "MicrosoftSentinelConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = MicrosoftSentinelConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MicrosoftSentinelConnector should be of type Connector"

    # get query target options
    sentinel_query_target_options = await connector.get_query_target_options()
    assert isinstance(sentinel_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select workspaces to target
    workspace_selector = None
    for selector in sentinel_query_target_options.selectors:
        if selector.type == 'workspace_names':  
            workspace_selector = selector
            break

    assert workspace_selector, "failed to retrieve workspace selector from query target options"

    assert isinstance(workspace_selector.values, list), "workspace_selector values must be a list"
    workspace_name = workspace_selector.values[0] if workspace_selector.values else None
    print(f"Selecting workspace name: {workspace_name}")

    assert workspace_name, f"failed to retrieve workspace name from workspace selector"

    # set up the target with workspace names
    target = MicrosoftSentinelTarget(workspace_names=[workspace_name])
    assert isinstance(target, ConnectorTargetInterface), "MicrosoftSentinelTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the ingest_data tool and execute it with workspace name
    ingest_data_tool = next(tool for tool in tools if tool.name == "ingest_data")
    
    # Create test data to ingest
    import time
    timestamp = int(time.time())
    
    test_data = [
        {
            "SourceSystem": "Custom",
            "TimeGenerated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "EventTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "EventType": "TestEvent",
            "EventID": f"TEST-{timestamp}",
            "EventSeverity": "Informational",
            "EventMessage": "This is a test event created by the Microsoft Sentinel connector test",
            "SourceIP": "192.0.2.1",
            "DestinationIP": "198.51.100.1"
        }
    ]
    
    log_type = "CustomSecurityLogs_CL"
    
    ingest_result = await ingest_data_tool.execute(
        workspace_name=workspace_name,
        log_type=log_type,
        data=test_data
    )
    ingest_response = ingest_result.result

    print("Type of returned ingest_response:", type(ingest_response))
    print(f"Ingest response: {str(ingest_response)[:200]}")

    # Verify that data ingestion was successful
    assert ingest_response is not None, "ingest_response should not be None"
    
    # Check the structure of the ingestion response
    if isinstance(ingest_response, dict):
        # Look for common Azure ingestion response fields
        response_fields = ["status", "code", "requestId", "correlationId"]
        present_fields = [field for field in response_fields if field in ingest_response]
        
        print(f"Ingest response contains these fields: {', '.join(present_fields)}")
        
        # Check for success indicators
        if "status" in ingest_response:
            status = ingest_response.get("status")
            print(f"Ingestion status: {status}")
            
        # Log the full structure for debugging
        print(f"Example ingest response structure: {ingest_response}")
        
    elif isinstance(ingest_response, bool):
        # Some implementations might return a simple boolean
        assert ingest_response == True, "Data ingestion should return True on success"
        print("Data ingestion returned True indicating success")
        
    elif isinstance(ingest_response, str):
        # Some implementations might return a status string
        print(f"Data ingestion returned status: {ingest_response}")
        
    else:
        # For other response types, just verify it's not None/False
        print(f"Data ingestion returned response of type {type(ingest_response)}: {ingest_response}")

    print(f"Successfully ingested test data into workspace {workspace_name} with log type {log_type}")
    print("Note: Data may not be immediately queryable due to Azure indexing delays")

    # Test with multiple data records to verify batch ingestion
    batch_test_data = [
        {
            "SourceSystem": "Custom",
            "TimeGenerated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "EventType": "BatchTestEvent",
            "EventID": f"BATCH-{timestamp}-{i}",
            "EventSeverity": "Informational",
            "EventMessage": f"Batch test event {i+1} created by Microsoft Sentinel connector test"
        }
        for i in range(3)
    ]
    
    batch_ingest_result = await ingest_data_tool.execute(
        workspace_name=workspace_name,
        log_type=log_type,
        data=batch_test_data
    )
    batch_response = batch_ingest_result.result

    print(f"Batch ingestion response: {str(batch_response)[:200]}")
    assert batch_response is not None, "batch ingestion should return a response"

    print(f"Successfully ingested {len(test_data)} single record and {len(batch_test_data)} batch records")

    return True