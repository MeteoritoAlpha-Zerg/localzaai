# 3-test_query_target_options.py

async def test_playbook_enumeration_options(zerg_state=None):
    """Test Revelstoke SOAR playbook and case enumeration by way of query target options"""
    print("Attempting to authenticate using Revelstoke SOAR connector")

    assert zerg_state, "this test requires valid zerg_state"

    revelstoke_url = zerg_state.get("revelstoke_url").get("value")
    revelstoke_api_key = zerg_state.get("revelstoke_api_key", {}).get("value")
    revelstoke_username = zerg_state.get("revelstoke_username", {}).get("value")
    revelstoke_password = zerg_state.get("revelstoke_password", {}).get("value")
    revelstoke_tenant_id = zerg_state.get("revelstoke_tenant_id", {}).get("value")

    from connectors.revelstoke.config import RevelstokeSoarConnectorConfig
    from connectors.revelstoke.connector import RevelstokeSoarConnector
    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    # prefer API key over username/password
    if revelstoke_api_key:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            api_key=revelstoke_api_key,
            tenant_id=revelstoke_tenant_id,
        )
    elif revelstoke_username and revelstoke_password:
        config = RevelstokeSoarConnectorConfig(
            url=revelstoke_url,
            username=revelstoke_username,
            password=revelstoke_password,
            tenant_id=revelstoke_tenant_id,
        )
    else:
        raise Exception("Either revelstoke_api_key or both revelstoke_username and revelstoke_password must be provided")

    assert isinstance(config, ConnectorConfig), "RevelstokeSoarConnectorConfig should be of type ConnectorConfig"

    connector = RevelstokeSoarConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RevelstokeSoarConnector should be of type Connector"

    revelstoke_query_target_options = await connector.get_query_target_options()
    assert isinstance(revelstoke_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert revelstoke_query_target_options, "Failed to retrieve query target options"

    print(f"revelstoke query target option definitions: {revelstoke_query_target_options.definitions}")
    print(f"revelstoke query target option selectors: {revelstoke_query_target_options.selectors}")

    return True