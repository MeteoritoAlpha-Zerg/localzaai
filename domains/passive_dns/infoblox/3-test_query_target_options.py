# 3-test_query_target_options.py

async def test_network_enumeration_options(zerg_state=None):
    """Test Infoblox network and DNS view enumeration by way of query target options"""
    print("Attempting to authenticate using Infoblox connector")

    assert zerg_state, "this test requires valid zerg_state"

    infoblox_url = zerg_state.get("infoblox_url").get("value")
    infoblox_username = zerg_state.get("infoblox_username").get("value")
    infoblox_password = zerg_state.get("infoblox_password").get("value")
    infoblox_wapi_version = zerg_state.get("infoblox_wapi_version").get("value")

    from connectors.infoblox.config import InfobloxConnectorConfig
    from connectors.infoblox.connector import InfobloxConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = InfobloxConnectorConfig(
        url=infoblox_url,
        username=infoblox_username,
        password=infoblox_password,
        wapi_version=infoblox_wapi_version,
    )
    assert isinstance(config, ConnectorConfig), "InfobloxConnectorConfig should be of type ConnectorConfig"

    connector = InfobloxConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "InfobloxConnector should be of type Connector"

    infoblox_query_target_options = await connector.get_query_target_options()
    assert isinstance(infoblox_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert infoblox_query_target_options, "Failed to retrieve query target options"

    print(f"infoblox query target option definitions: {infoblox_query_target_options.definitions}")
    print(f"infoblox query target option selectors: {infoblox_query_target_options.selectors}")

    return True