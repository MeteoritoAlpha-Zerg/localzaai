# 3-test_query_target_options.py

async def test_investigation_team_enumeration_options(zerg_state=None):
    """Test Cortex XSOAR investigation team enumeration by way of query target options"""
    print("Attempting to authenticate using Cortex XSOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    xsoar_server_url = zerg_state.get("xsoar_server_url").get("value")
    xsoar_api_key = zerg_state.get("xsoar_api_key").get("value")
    xsoar_api_key_id = zerg_state.get("xsoar_api_key_id").get("value")

    from connectors.xsoar.config import XSOARConnectorConfig
    from connectors.xsoar.connector import XSOARConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = XSOARConnectorConfig(
        server_url=xsoar_server_url,
        api_key=xsoar_api_key,
        api_key_id=xsoar_api_key_id,
    )
    assert isinstance(config, ConnectorConfig), "XSOARConnectorConfig should be of type ConnectorConfig"

    connector = XSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "XSOARConnector should be of type Connector"

    xsoar_query_target_options = await connector.get_query_target_options()
    assert isinstance(xsoar_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert xsoar_query_target_options, "Failed to retrieve query target options"

    print(f"Cortex XSOAR query target option definitions: {xsoar_query_target_options.definitions}")
    print(f"Cortex XSOAR query target option selectors: {xsoar_query_target_options.selectors}")

    return True