# 3-test_query_target_options.py

async def test_security_manager_enumeration_options(zerg_state=None):
    """Test ArcSight security manager enumeration by way of query target options"""
    print("Attempting to authenticate using ArcSight connector")

    assert zerg_state, "this test requires valid zerg_state"

    arcsight_server_url = zerg_state.get("arcsight_server_url").get("value")
    arcsight_username = zerg_state.get("arcsight_username").get("value")
    arcsight_password = zerg_state.get("arcsight_password").get("value")

    from connectors.arcsight.config import ArcSightConnectorConfig
    from connectors.arcsight.connector import ArcSightConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = ArcSightConnectorConfig(
        server_url=arcsight_server_url,
        username=arcsight_username,
        password=arcsight_password,
    )
    assert isinstance(config, ConnectorConfig), "ArcSightConnectorConfig should be of type ConnectorConfig"

    connector = ArcSightConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ArcSightConnector should be of type Connector"

    arcsight_query_target_options = await connector.get_query_target_options()
    assert isinstance(arcsight_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert arcsight_query_target_options, "Failed to retrieve query target options"

    print(f"ArcSight query target option definitions: {arcsight_query_target_options.definitions}")
    print(f"ArcSight query target option selectors: {arcsight_query_target_options.selectors}")

    return True