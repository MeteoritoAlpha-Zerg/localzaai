# 3-test_query_target_options.py

async def test_organization_enumeration_options(zerg_state=None):
    """Test OpenDNS organization enumeration by way of query target options"""
    print("Attempting to authenticate using OpenDNS (Cisco Umbrella) connector")

    assert zerg_state, "this test requires valid zerg_state"

    opendns_api_key = zerg_state.get("opendns_api_key").get("value")
    opendns_api_secret = zerg_state.get("opendns_api_secret").get("value")
    opendns_organization_id = zerg_state.get("opendns_organization_id").get("value")

    from connectors.opendns.config import OpenDNSConnectorConfig
    from connectors.opendns.connector import OpenDNSConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = OpenDNSConnectorConfig(
        api_key=opendns_api_key,
        api_secret=opendns_api_secret,
        organization_id=opendns_organization_id,
    )
    assert isinstance(config, ConnectorConfig), "OpenDNSConnectorConfig should be of type ConnectorConfig"

    connector = OpenDNSConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "OpenDNSConnector should be of type Connector"

    opendns_query_target_options = await connector.get_query_target_options()
    assert isinstance(opendns_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert opendns_query_target_options, "Failed to retrieve query target options"

    print(f"OpenDNS query target option definitions: {opendns_query_target_options.definitions}")
    print(f"OpenDNS query target option selectors: {opendns_query_target_options.selectors}")

    return True