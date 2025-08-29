# 6-test_send_message.py

async def test_send_message(zerg_state=None):
    """Test Signal message sending to selected group"""
    print("Attempting to authenticate using Signal connector")

    assert zerg_state, "this test requires valid zerg_state"

    signal_api_url = zerg_state.get("signal_api_url").get("value")
    signal_phone_number = zerg_state.get("signal_phone_number").get("value")
    signal_api_key = zerg_state.get("signal_api_key").get("value")

    from connectors.signal.config import SignalConnectorConfig
    from connectors.signal.connector import SignalConnector
    from connectors.signal.tools import SignalConnectorTools, SendSignalMessageInput
    from connectors.signal.target import SignalTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = SignalConnectorConfig(
        api_url=signal_api_url,
        phone_number=signal_phone_number,
        api_key=signal_api_key
    )
    assert isinstance(config, ConnectorConfig), "SignalConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = SignalConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SignalConnectorConfig should be of type ConnectorConfig"

    # get query target options
    signal_query_target_options = await connector.get_query_target_options()
    assert isinstance(signal_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select group to target
    group_selector = None
    for selector in signal_query_target_options.selectors:
        if selector.type == 'group_ids':  
            group_selector = selector
            break

    assert group_selector, "failed to retrieve group selector from query target options"

    assert isinstance(group_selector.values, list), "group_selector values must be a list"
    group_id = group_selector.values[0] if group_selector.values else None
    print(f"Selecting group id: {group_id}")

    assert group_id, f"failed to retrieve group id from group selector"

    # set up the target with group id
    target = SignalTarget(group_ids=[group_id])
    assert isinstance(target, ConnectorTargetInterface), "SignalTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the send_signal_message tool and execute it with group id and test message
    send_signal_message_tool = next(tool for tool in tools if tool.name == "send_signal_message")
    test_message = f"Test message from Signal connector at {datetime.now().isoformat()}"
    
    send_result = await send_signal_message_tool.execute(
        group_id=group_id,
        message=test_message
    )
    send_response = send_result.result

    print("Type of returned send_response:", type(send_response))
    print(f"Send response: {send_response}")

    # Verify that the message was sent successfully
    assert isinstance(send_response, dict), "send_response should be a dict"
    
    # Verify essential response fields
    assert "success" in send_response, "Response should have a 'success' field"
    assert send_response["success"] is True, "Message send should be successful"
    
    # Check for additional response fields that indicate successful delivery
    expected_fields = ["message_id", "timestamp", "group_id"]
    for field in expected_fields:
        if field in send_response:
            print(f"Response contains field '{field}': {send_response[field]}")
            
            # Verify group_id matches if present
            if field == "group_id":
                assert send_response[field] == group_id, f"Response group_id should match requested group_id"
    
    # Verify at least one of the expected fields is present (indicating proper API response)
    present_fields = [field for field in expected_fields if field in send_response]
    assert len(present_fields) > 0, "Response should contain at least one of: message_id, timestamp, or group_id"

    print(f"Successfully sent message to Signal group {group_id}")
    print(f"Response structure: {send_response}")

    return True