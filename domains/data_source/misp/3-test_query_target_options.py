# 3-test_query_target_options.py

async def test_organization_enumeration_options(zerg_state=None):
    """Test MISP organization enumeration by way of query target options"""
    print("Attempting to authenticate using MISP connector")

    assert zerg_state, "this test requires valid zerg_state"

    misp_url = zerg_state.get("misp_url").get("value")
    misp_api_key = zerg_state.get("misp_api_key").get("value")

    from connectors.misp.config import MISPConnectorConfig
    from connectors.misp.connector import MISPConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = MISPConnectorConfig(
        url=misp_url,
        api_key=misp_api_key,
    )
    assert isinstance(config, ConnectorConfig), "MISPConnectorConfig should be of type ConnectorConfig"

    connector = MISPConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "MISPConnector should be of type Connector"

    misp_query_target_options = await connector.get_query_target_options()
    assert isinstance(misp_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert misp_query_target_options, "Failed to retrieve query target options"

    print(f"MISP query target option definitions: {misp_query_target_options.definitions}")
    print(f"MISP query target option selectors: {misp_query_target_options.selectors}")

    return True