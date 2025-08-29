# 3-test_query_target_options.py

async def test_service_request_enumeration_options(zerg_state=None):
    """Test SysAid service request enumeration by way of query target options"""
    print("Attempting to authenticate using SysAid connector")

    assert zerg_state, "this test requires valid zerg_state"

    sysaid_url = zerg_state.get("sysaid_url").get("value")
    sysaid_account_id = zerg_state.get("sysaid_account_id").get("value")
    sysaid_username = zerg_state.get("sysaid_username").get("value")
    sysaid_password = zerg_state.get("sysaid_password").get("value")

    from connectors.sysaid.config import SysAidConnectorConfig
    from connectors.sysaid.connector import SysAidConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SysAidConnectorConfig(
        url=sysaid_url,
        account_id=sysaid_account_id,
        username=sysaid_username,
        password=sysaid_password,
    )
    assert isinstance(config, ConnectorConfig), "SysAidConnectorConfig should be of type ConnectorConfig"

    connector = SysAidConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SysAidConnector should be of type Connector"

    sysaid_query_target_options = await connector.get_query_target_options()
    assert isinstance(sysaid_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert sysaid_query_target_options, "Failed to retrieve query target options"

    print(f"sysaid query target option definitions: {sysaid_query_target_options.definitions}")
    print(f"sysaid query target option selectors: {sysaid_query_target_options.selectors}")

    return True