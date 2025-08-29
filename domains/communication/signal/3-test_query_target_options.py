# 3-test_query_target_options.py

async def test_group_enumeration_options(zerg_state=None):
    """Test Signal group enumeration by way of query target options"""
    print("Attempting to authenticate using Signal connector")

    assert zerg_state, "this test requires valid zerg_state"

    signal_api_url = zerg_state.get("signal_api_url").get("value")
    signal_phone_number = zerg_state.get("signal_phone_number").get("value")
    signal_api_key = zerg_state.get("signal_api_key").get("value")

    from connectors.signal.config import SignalConnectorConfig
    from connectors.signal.connector import SignalConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SignalConnectorConfig(
        api_url=signal_api_url,
        phone_number=signal_phone_number,
        api_key=signal_api_key,
    )
    assert isinstance(config, ConnectorConfig), "SignalConnectorConfig should be of type ConnectorConfig"

    connector = SignalConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SignalConnectorConfig should be of type ConnectorConfig"

    signal_query_target_options = await connector.get_query_target_options()
    assert isinstance(signal_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert signal_query_target_options, "Failed to retrieve query target options"

    print(f"signal query target option definitions: {signal_query_target_options.definitions}")
    print(f"signal query target option selectors: {signal_query_target_options.selectors}")

    return True