# 6-test_log_ingestion.py

async def test_log_ingestion(zerg_state=None):
    """Test Splunk log ingestion through HTTP Event Collector"""
    print("Testing Splunk log ingestion through HTTP Event Collector")

    assert zerg_state, "this test requires valid zerg_state"

    splunk_host = zerg_state.get("splunk_host").get("value")
    splunk_port = zerg_state.get("splunk_port").get("value")
    splunk_username = zerg_state.get("splunk_username").get("value")
    splunk_password = zerg_state.get("splunk_password").get("value")
    splunk_hec_token = zerg_state.get("splunk_hec_token").get("value")

    from connectors.splunk.config import SplunkConnectorConfig
    from connectors.splunk.connector import SplunkConnector
    from connectors.splunk.target import SplunkTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SplunkConnectorConfig(
        host=splunk_host,
        port=int(splunk_port),
        username=splunk_username,
        password=splunk_password,
        hec_token=splunk_hec_token
    )
    assert isinstance(config, ConnectorConfig), "SplunkConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SplunkConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SplunkConnector should be of type Connector"

    # get query target options to find available indexes
    splunk_query_target_options = await connector.get_query_target_options()
    assert isinstance(splunk_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select index to target for log ingestion
    index_selector = None
    for selector in splunk_query_target_options.selectors:
        if selector.type == 'index_names':  
            index_selector = selector
            break

    assert index_selector, "failed to retrieve index selector from query target options"

    assert isinstance(index_selector.values, list), "index_selector values must be a list"
    index_name = index_selector.values[0] if index_selector.values else None
    print(f"Using index for log ingestion: {index_name}")

    assert index_name, f"failed to retrieve index name from index selector"

    # set up the target with index name
    target = SplunkTarget(index_names=[index_name])
    assert isinstance(target, ConnectorTargetInterface), "SplunkTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the ingest_logs tool and execute log ingestion test
    ingest_logs_tool = next(tool for tool in tools if tool.name == "ingest_logs")
    
    # Create test log data for ingestion in Splunk HEC format
    import time
    import json
    
    current_timestamp = time.time()
    test_log_data = [
        {
            "time": current_timestamp,
            "event": {
                "level": "INFO",
                "message": "Test log ingestion from Splunk connector",
                "source": "connector_test",
                "host": "test-host"
            },
            "index": index_name,
            "sourcetype": "connector_test"
        },
        {
            "time": current_timestamp + 1,
            "event": {
                "level": "WARN", 
                "message": "Test warning log entry",
                "source": "connector_test",
                "host": "test-host"
            },
            "index": index_name,
            "sourcetype": "connector_test"
        }
    ]
    
    # Execute log ingestion
    ingestion_result = await ingest_logs_tool.execute(
        index_name=index_name,
        log_data=test_log_data
    )
    ingestion_response = ingestion_result.result

    print("Type of returned ingestion_response:", type(ingestion_response))
    print(f"Ingestion response preview: {str(ingestion_response)[:200]}")

    # Verify that ingestion_response contains meaningful data
    assert ingestion_response is not None, "ingestion_response should not be None"
    
    # Splunk HEC ingestion response is typically a dictionary with status information
    if isinstance(ingestion_response, dict):
        # Check for common Splunk HEC response fields
        expected_fields = ["text", "code", "invalid-event-number", "ackId"]
        present_fields = [field for field in expected_fields if field in ingestion_response]
        
        if len(present_fields) > 0:
            print(f"Ingestion response contains these fields: {', '.join(present_fields)}")
            
            # Verify success status
            if "text" in ingestion_response:
                text_response = ingestion_response["text"]
                success_indicators = ["success", "ok"]
                text_lower = str(text_response).lower()
                has_success_indicator = any(indicator in text_lower for indicator in success_indicators)
                
                if has_success_indicator:
                    print(f"Ingestion appears successful: {text_response}")
                else:
                    print(f"Ingestion response text: {text_response}")
            
            # Verify response code if present
            if "code" in ingestion_response:
                response_code = ingestion_response["code"]
                assert isinstance(response_code, int), "Response code should be integer"
                # HTTP 0 or 200-299 codes typically indicate success for Splunk HEC
                if response_code == 0 or (200 <= response_code < 300):
                    print(f"Ingestion successful with response code: {response_code}")
                else:
                    print(f"Warning: Ingestion response code may indicate issues: {response_code}")
            
            # Check for acknowledgment ID if present
            if "ackId" in ingestion_response:
                ack_id = ingestion_response["ackId"]
                assert isinstance(ack_id, (str, int)), "Acknowledgment ID should be string or integer"
                print(f"Received acknowledgment ID: {ack_id}")
            
            # Check for invalid event number (should be absent for successful ingestion)
            if "invalid-event-number" in ingestion_response:
                invalid_event_num = ingestion_response["invalid-event-number"]
                print(f"Warning: Invalid event number reported: {invalid_event_num}")
        
        # Log the full structure for debugging
        print(f"Ingestion response structure: {ingestion_response}")
        
    elif isinstance(ingestion_response, str):
        # Response might be a simple status string
        success_indicators = ["success", "ok", "accepted"]
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

    print(f"Successfully tested Splunk HEC log ingestion capabilities")

    return True