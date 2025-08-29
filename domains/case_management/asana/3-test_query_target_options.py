# 3-test_query_target_options.py

async def test_workspace_enumeration_options(zerg_state=None):
    """Test Asana workspace enumeration by way of query target options"""
    print("Attempting to authenticate using Asana connector")

    assert zerg_state, "this test requires valid zerg_state"

    asana_personal_access_token = zerg_state.get("asana_personal_access_token").get("value")

    from connectors.asana.config import AsanaConnectorConfig
    from connectors.asana.connector import AsanaConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = AsanaConnectorConfig(
        personal_access_token=asana_personal_access_token,
    )
    assert isinstance(config, ConnectorConfig), "AsanaConnectorConfig should be of type ConnectorConfig"

    connector = AsanaConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "AsanaConnector should be of type Connector"

    asana_query_target_options = await connector.get_query_target_options()
    assert isinstance(asana_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert asana_query_target_options, "Failed to retrieve query target options"

    print(f"asana query target option definitions: {asana_query_target_options.definitions}")
    print(f"asana query target option selectors: {asana_query_target_options.selectors}")

    return True