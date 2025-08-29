# 3-test_query_target_options.py

async def test_model_enumeration_options(zerg_state=None):
    """Test Darktrace model and device enumeration by way of query target options"""
    print("Attempting to authenticate using Darktrace connector")

    assert zerg_state, "this test requires valid zerg_state"

    darktrace_url = zerg_state.get("darktrace_url").get("value")
    darktrace_public_token = zerg_state.get("darktrace_public_token").get("value")
    darktrace_private_token = zerg_state.get("darktrace_private_token").get("value")

    from connectors.darktrace.config import DarktraceConnectorConfig
    from connectors.darktrace.connector import DarktraceConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = DarktraceConnectorConfig(
        url=darktrace_url,
        public_token=darktrace_public_token,
        private_token=darktrace_private_token,
    )
    assert isinstance(config, ConnectorConfig), "DarktraceConnectorConfig should be of type ConnectorConfig"

    connector = DarktraceConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DarktraceConnector should be of type Connector"

    darktrace_query_target_options = await connector.get_query_target_options()
    assert isinstance(darktrace_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert darktrace_query_target_options, "Failed to retrieve query target options"

    print(f"darktrace query target option definitions: {darktrace_query_target_options.definitions}")
    print(f"darktrace query target option selectors: {darktrace_query_target_options.selectors}")

    return True