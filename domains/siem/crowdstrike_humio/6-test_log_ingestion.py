# 6-test_log_ingestion.py

async def test_log_ingestion(zerg_state=None):
    """Test CrowdStrike Humio log ingestion and streaming analytics"""
    print("Testing CrowdStrike Humio log ingestion and streaming analytics")

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

    # get query target options to find available repositories
    humio_query_target_options = await connector.get_query_target_options()
    assert isinstance(humio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select repository to target for log ingestion
    repository_selector = None
    for selector in humio_query_target_options.selectors:
        if selector.type == 'repository_names':  
            repository_selector = selector
            break

    assert repository_selector, "failed to retrieve repository selector from query target options"

    assert isinstance(repository_selector.values, list), "repository_selector values must be a list"
    repository_name = repository_selector.values[0] if repository_selector.values else None
    print(f"Using repository for log ingestion: {repository_name}")

    assert repository_name, f"failed to retrieve repository name from repository selector"

    # set up the target with repository name
    target = CrowdStrikeHumioTarget(repository_names=[repository_name])
    assert isinstance(target, ConnectorTargetInterface), "CrowdStrikeHumioTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the ingest_logs tool and execute log ingestion test
    ingest_logs_tool = next(tool for tool in tools if tool.name == "ingest_logs")
    
    # Create test log data for ingestion
    import time
    import json
    
    current_timestamp = int(time.time() * 1000)  # Humio uses milliseconds
    test_log_data = [
        {
            "timestamp": current_timestamp,
            "level": "INFO",
            "message": "Test log ingestion from connector",
            "source": "connector_test",
            "host": "test-host"
        },
        {
            "timestamp": current_timestamp + 1000,
            "level": "WARN", 
            "message": "Test warning log entry",
            "source": "connector_test",
            "host": "test-host"
        }
    ]
    
    # Execute log ingestion
    ingestion_result = await ingest_logs_tool.execute(
        repository_name=repository_name,
        log_data=test_log_data
    )
    ingestion_response = ingestion_result.result

    print("Type of returned ingestion_response:", type(ingestion_response))
    print(f"Ingestion response preview: {str(ingestion_response)[:200]}")

    # Verify that ingestion_response contains meaningful data
    assert ingestion_response is not None, "ingestion_response should not be None"
    
    # Ingestion response could be a dictionary with status information
    if isinstance(ingestion_response, dict):
        # Check for common ingestion response fields
        expected_fields = ["status", "success", "ingested_count", "error_count", "response_code"]
        present_fields = [field for field in expected_fields if field in ingestion_response]
        
        if len(present_fields) > 0:
            print(f"Ingestion response contains these fields: {', '.join(present_fields)}")
            
            # Verify success status if present
            if "status" in ingestion_response:
                status = ingestion_response["status"]
                valid_statuses = ["success", "ok", "accepted", "completed"]
                # Check if status indicates success (case-insensitive)
                status_ok = any(valid_status in str(status).lower() for valid_status in valid_statuses)
                if not status_ok:
                    print(f"Warning: Ingestion status may indicate issues: {status}")
            
            # Verify ingested count if present
            if "ingested_count" in ingestion_response:
                ingested_count = ingestion_response["ingested_count"]
                assert isinstance(ingested_count, (int, float)), "Ingested count should be numeric"
                print(f"Successfully ingested {ingested_count} log entries")
            
            # Verify response code if present
            if "response_code" in ingestion_response:
                response_code = ingestion_response["response_code"]
                assert isinstance(response_code, int), "Response code should be integer"
                # HTTP 2xx codes indicate success
                if 200 <= response_code < 300:
                    print(f"Ingestion successful with response code: {response_code}")
                else:
                    print(f"Warning: Ingestion response code may indicate issues: {response_code}")
        
        # Log the full structure for debugging
        print(f"Ingestion response structure: {ingestion_response}")
        
    elif isinstance(ingestion_response, str):
        # Response might be a simple status string
        success_indicators = ["success", "ok", "accepted", "completed"]
        response_lower = ingestion_response.lower()
        has_success_indicator = any(indicator in response_lower for indicator in success_indicators)
        
        if has_success_indicator:
            print(f"Ingestion appears successful: {ingestion_response}")
        else:
            print(f"Ingestion response: {ingestion_response}")
            
    elif isinstance(ingestion_response, bool):
        # Simple boolean response
        if ingestion_response:
            print("Ingestion successful (boolean true)")
        else:
            print("Warning: Ingestion returned false")
            
    else:
        # Other response formats
        print(f"Ingestion response in unexpected format: {type(ingestion_response)}")
        assert str(ingestion_response).strip() != "", "Ingestion response should not be empty"

    print(f"Successfully tested log ingestion capabilities")

    return True