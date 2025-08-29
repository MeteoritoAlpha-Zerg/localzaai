# 3-test_query_target_options.py

async def test_company_enumeration_options(zerg_state=None):
    """Test BitSight company and portfolio enumeration by way of query target options"""
    print("Attempting to authenticate using BitSight connector")

    assert zerg_state, "this test requires valid zerg_state"

    bitsight_url = zerg_state.get("bitsight_url").get("value")
    bitsight_api_token = zerg_state.get("bitsight_api_token").get("value")

    from connectors.bitsight.config import BitSightConnectorConfig
    from connectors.bitsight.connector import BitSightConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = BitSightConnectorConfig(
        url=bitsight_url,
        api_token=bitsight_api_token,
    )
    assert isinstance(config, ConnectorConfig), "BitSightConnectorConfig should be of type ConnectorConfig"

    connector = BitSightConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "BitSightConnector should be of type Connector"

    bitsight_query_target_options = await connector.get_query_target_options()
    assert isinstance(bitsight_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert bitsight_query_target_options, "Failed to retrieve query target options"

    print(f"bitsight query target option definitions: {bitsight_query_target_options.definitions}")
    print(f"bitsight query target option selectors: {bitsight_query_target_options.selectors}")

    return True