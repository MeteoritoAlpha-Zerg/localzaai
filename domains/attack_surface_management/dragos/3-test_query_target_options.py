# 3-test_query_target_options.py

async def test_threat_feed_enumeration_options(zerg_state=None):
    """Test Dragos OT threat intelligence feed enumeration by way of query target options"""
    print("Attempting to authenticate using Dragos connector")

    assert zerg_state, "this test requires valid zerg_state"

    dragos_api_url = zerg_state.get("dragos_api_url").get("value")
    dragos_api_key = zerg_state.get("dragos_api_key").get("value")
    dragos_api_secret = zerg_state.get("dragos_api_secret").get("value")
    dragos_client_id = zerg_state.get("dragos_client_id").get("value")
    dragos_api_version = zerg_state.get("dragos_api_version").get("value")

    from connectors.dragos.config import DragosConnectorConfig
    from connectors.dragos.connector import DragosConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = DragosConnectorConfig(
        api_url=dragos_api_url,
        api_key=dragos_api_key,
        api_secret=dragos_api_secret,
        client_id=dragos_client_id,
        api_version=dragos_api_version,
    )
    assert isinstance(config, ConnectorConfig), "DragosConnectorConfig should be of type ConnectorConfig"

    connector = DragosConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DragosConnector should be of type Connector"

    dragos_query_target_options = await connector.get_query_target_options()
    assert isinstance(dragos_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert dragos_query_target_options, "Failed to retrieve query target options"

    print(f"dragos query target option definitions: {dragos_query_target_options.definitions}")
    print(f"dragos query target option selectors: {dragos_query_target_options.selectors}")

    return True