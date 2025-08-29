# 3-test_query_target_options.py

async def test_api_root_collection_enumeration_options(zerg_state=None):
    """Test TAXII API root and collection enumeration by way of query target options"""
    print("Attempting to authenticate using STIX/TAXII connector")

    assert zerg_state, "this test requires valid zerg_state"

    taxii_server_url = zerg_state.get("taxii_server_url").get("value")
    taxii_username = zerg_state.get("taxii_username").get("value")
    taxii_password = zerg_state.get("taxii_password").get("value")

    from connectors.stix_taxii.config import STIXTAXIIConnectorConfig
    from connectors.stix_taxii.connector import STIXTAXIIConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = STIXTAXIIConnectorConfig(
        server_url=taxii_server_url,
        username=taxii_username,
        password=taxii_password,
    )
    assert isinstance(config, ConnectorConfig), "STIXTAXIIConnectorConfig should be of type ConnectorConfig"

    connector = STIXTAXIIConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "STIXTAXIIConnector should be of type Connector"

    stix_taxii_query_target_options = await connector.get_query_target_options()
    assert isinstance(stix_taxii_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert stix_taxii_query_target_options, "Failed to retrieve query target options"

    print(f"STIX/TAXII query target option definitions: {stix_taxii_query_target_options.definitions}")
    print(f"STIX/TAXII query target option selectors: {stix_taxii_query_target_options.selectors}")

    return True