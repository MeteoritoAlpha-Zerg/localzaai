# 3-test_query_target_options.py

async def test_application_workspace_enumeration_options(zerg_state=None):
    """Test Swimlane SOAR application and workspace enumeration by way of query target options"""
    print("Attempting to authenticate using Swimlane SOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    swimlane_host = zerg_state.get("swimlane_host").get("value")
    swimlane_api_token = zerg_state.get("swimlane_api_token").get("value")
    swimlane_user_id = zerg_state.get("swimlane_user_id").get("value")

    from connectors.swimlane_soar.config import SwimlaneSOARConnectorConfig
    from connectors.swimlane_soar.connector import SwimlaneSOARConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SwimlaneSOARConnectorConfig(
        host=swimlane_host,
        api_token=swimlane_api_token,
        user_id=swimlane_user_id,
    )
    assert isinstance(config, ConnectorConfig), "SwimlaneSOARConnectorConfig should be of type ConnectorConfig"

    connector = SwimlaneSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SwimlaneSOARConnector should be of type Connector"

    swimlane_query_target_options = await connector.get_query_target_options()
    assert isinstance(swimlane_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert swimlane_query_target_options, "Failed to retrieve query target options"

    print(f"Swimlane SOAR query target option definitions: {swimlane_query_target_options.definitions}")
    print(f"Swimlane SOAR query target option selectors: {swimlane_query_target_options.selectors}")

    return True