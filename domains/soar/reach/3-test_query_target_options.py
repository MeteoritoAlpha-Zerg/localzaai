# 3-test_query_target_options.py

async def test_workflow_playbook_enumeration_options(zerg_state=None):
    """Test Reach SOAR workflow and playbook enumeration by way of query target options"""
    print("Attempting to authenticate using Reach SOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    reach_soar_api_token = zerg_state.get("reach_soar_api_token").get("value")
    reach_soar_base_url = zerg_state.get("reach_soar_base_url").get("value")
    reach_soar_tenant_id = zerg_state.get("reach_soar_tenant_id").get("value")

    from connectors.reach_soar.config import ReachSOARConnectorConfig
    from connectors.reach_soar.connector import ReachSOARConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = ReachSOARConnectorConfig(
        api_token=reach_soar_api_token,
        base_url=reach_soar_base_url,
        tenant_id=reach_soar_tenant_id,
    )
    assert isinstance(config, ConnectorConfig), "ReachSOARConnectorConfig should be of type ConnectorConfig"

    connector = ReachSOARConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ReachSOARConnector should be of type Connector"

    reach_soar_query_target_options = await connector.get_query_target_options()
    assert isinstance(reach_soar_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert reach_soar_query_target_options, "Failed to retrieve query target options"

    print(f"Reach SOAR query target option definitions: {reach_soar_query_target_options.definitions}")
    print(f"Reach SOAR query target option selectors: {reach_soar_query_target_options.selectors}")

    return True