# 3-test_query_target_options.py

async def test_source_enumeration_options(zerg_state=None):
    """Test ThreatConnect source and group enumeration by way of query target options"""
    print("Attempting to authenticate using ThreatConnect connector")

    assert zerg_state, "this test requires valid zerg_state"

    threatconnect_url = zerg_state.get("threatconnect_url").get("value")
    threatconnect_access_id = zerg_state.get("threatconnect_access_id").get("value")
    threatconnect_secret_key = zerg_state.get("threatconnect_secret_key").get("value")
    threatconnect_default_org = zerg_state.get("threatconnect_default_org").get("value")

    from connectors.threatconnect.config import ThreatConnectConnectorConfig
    from connectors.threatconnect.connector import ThreatConnectConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = ThreatConnectConnectorConfig(
        url=threatconnect_url,
        access_id=threatconnect_access_id,
        secret_key=threatconnect_secret_key,
        default_org=threatconnect_default_org,
    )
    assert isinstance(config, ConnectorConfig), "ThreatConnectConnectorConfig should be of type ConnectorConfig"

    connector = ThreatConnectConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ThreatConnectConnector should be of type Connector"

    threatconnect_query_target_options = await connector.get_query_target_options()
    assert isinstance(threatconnect_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert threatconnect_query_target_options, "Failed to retrieve query target options"

    print(f"threatconnect query target option definitions: {threatconnect_query_target_options.definitions}")
    print(f"threatconnect query target option selectors: {threatconnect_query_target_options.selectors}")

    return True