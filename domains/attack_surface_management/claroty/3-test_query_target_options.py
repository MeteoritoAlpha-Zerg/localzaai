# 3-test_query_target_options.py

async def test_asset_type_enumeration_options(zerg_state=None):
    """Test Claroty asset type and security zone enumeration by way of query target options"""
    print("Attempting to authenticate using Claroty connector")

    assert zerg_state, "this test requires valid zerg_state"

    claroty_server_url = zerg_state.get("claroty_server_url").get("value")
    claroty_api_token = zerg_state.get("claroty_api_token").get("value")
    claroty_username = zerg_state.get("claroty_username").get("value")
    claroty_password = zerg_state.get("claroty_password").get("value")
    claroty_api_version = zerg_state.get("claroty_api_version").get("value")

    from connectors.claroty.config import ClarotyConnectorConfig
    from connectors.claroty.connector import ClarotyConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = ClarotyConnectorConfig(
        server_url=claroty_server_url,
        api_token=claroty_api_token,
        username=claroty_username,
        password=claroty_password,
        api_version=claroty_api_version,
    )
    assert isinstance(config, ConnectorConfig), "ClarotyConnectorConfig should be of type ConnectorConfig"

    connector = ClarotyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ClarotyConnector should be of type Connector"

    claroty_query_target_options = await connector.get_query_target_options()
    assert isinstance(claroty_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert claroty_query_target_options, "Failed to retrieve query target options"

    print(f"claroty query target option definitions: {claroty_query_target_options.definitions}")
    print(f"claroty query target option selectors: {claroty_query_target_options.selectors}")

    return True