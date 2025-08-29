# 3-test_query_target_options.py

async def test_index_app_enumeration_options(zerg_state=None):
    """Test Splunk index and app enumeration by way of query target options"""
    print("Attempting to authenticate using Splunk connector")

    assert zerg_state, "this test requires valid zerg_state"

    splunk_host = zerg_state.get("splunk_host").get("value")
    splunk_port = zerg_state.get("splunk_port").get("value")
    splunk_username = zerg_state.get("splunk_username").get("value")
    splunk_password = zerg_state.get("splunk_password").get("value")
    splunk_hec_token = zerg_state.get("splunk_hec_token").get("value")

    from connectors.splunk.config import SplunkConnectorConfig
    from connectors.splunk.connector import SplunkConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SplunkConnectorConfig(
        host=splunk_host,
        port=int(splunk_port),
        username=splunk_username,
        password=splunk_password,
        hec_token=splunk_hec_token,
    )
    assert isinstance(config, ConnectorConfig), "SplunkConnectorConfig should be of type ConnectorConfig"

    connector = SplunkConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SplunkConnector should be of type Connector"

    splunk_query_target_options = await connector.get_query_target_options()
    assert isinstance(splunk_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert splunk_query_target_options, "Failed to retrieve query target options"

    print(f"Splunk query target option definitions: {splunk_query_target_options.definitions}")
    print(f"Splunk query target option selectors: {splunk_query_target_options.selectors}")

    return True