# 5-test_message_retrieval.py

async def test_message_retrieval(zerg_state=None):
    """Test Signal message retrieval for selected group"""
    print("Attempting to authenticate using Signal connector")

    assert zerg_state, "this test requires valid zerg_state"

    signal_api_url = zerg_state.get("signal_api_url").get("value")
    signal_phone_number = zerg_state.get("signal_phone_number").get("value")
    signal_api_key = zerg_state.get("signal_api_key").get("value")

    from connectors.signal.config import SignalConnectorConfig
    from connectors.signal.connector import SignalConnector
    from connectors.signal.tools import SignalConnectorTools, GetSignalMessagesInput
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

    # grab the get_signal_messages tool and execute it with group id
    get_signal_messages_tool = next(tool for tool in tools if tool.name == "get_signal_messages")
    signal_messages_result = await get_signal_messages_tool.execute(group_id=group_id)
    signal_messages = signal_messages_result.result

    print("Type of returned signal_messages:", type(signal_messages))
    print(f"len messages: {len(signal_messages)} messages: {str(signal_messages)[:200]}")

    # Verify that signal_messages is a list
    assert isinstance(signal_messages, list), "signal_messages should be a list"
    assert len(signal_messages) > 0, "signal_messages should not be empty"
    
    # Limit the number of messages to check if there are many
    messages_to_check = signal_messages[:5] if len(signal_messages) > 5 else signal_messages
    
    # Verify structure of each message object
    for message in messages_to_check:
        # Verify essential Signal message fields
        assert "id" in message, "Each message should have an 'id' field"
        assert "timestamp" in message, "Each message should have a 'timestamp' field"
        assert "sender" in message, "Each message should have a 'sender' field"
        assert "group_id" in message, "Each message should have a 'group_id' field"
        
        # Check if message belongs to the requested group
        assert message["group_id"] == group_id, f"Message {message['id']} does not belong to the requested group_id"
        
        # Verify common Signal message fields
        assert "text" in message or "attachments" in message, "Each message should have either 'text' or 'attachments'"
        
        # Check for additional optional fields
        optional_fields = ["quote", "reactions", "mentions", "edit_timestamp", "type"]
        present_optional = [field for field in optional_fields if field in message]
        
        print(f"Message {message['id']} contains these optional fields: {', '.join(present_optional)}")
        
        # Log the structure of the first message for debugging
        if message == messages_to_check[0]:
            print(f"Example message structure: {message}")

    print(f"Successfully retrieved and validated {len(signal_messages)} Signal messages")

    return True