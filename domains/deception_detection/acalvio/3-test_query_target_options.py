# 3-test_query_target_options.py

async def test_environment_enumeration_options(zerg_state=None):
    """Test Acalvio deception environment enumeration by way of query target options"""
    print("Attempting to authenticate using Acalvio connector")

    assert zerg_state, "this test requires valid zerg_state"

    acalvio_api_url = zerg_state.get("acalvio_api_url").get("value")
    acalvio_api_key = zerg_state.get("acalvio_api_key").get("value")
    acalvio_username = zerg_state.get("acalvio_username").get("value")
    acalvio_password = zerg_state.get("acalvio_password").get("value")
    acalvio_tenant_id = zerg_state.get("acalvio_tenant_id").get("value")

    from connectors.acalvio.config import AcalvioConnectorConfig
    from connectors.acalvio.connector import AcalvioConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = AcalvioConnectorConfig(
        api_url=acalvio_api_url,
        api_key=acalvio_api_key,
        username=acalvio_username,
        password=acalvio_password,
        tenant_id=acalvio_tenant_id,
    )
    assert isinstance(config, ConnectorConfig), "AcalvioConnectorConfig should be of type ConnectorConfig"

    connector = AcalvioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "AcalvioConnectorConfig should be of type ConnectorConfig"

    acalvio_query_target_options = await connector.get_query_target_options()
    assert isinstance(acalvio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert acalvio_query_target_options, "Failed to retrieve query target options"

    print(f"acalvio query target option definitions: {acalvio_query_target_options.definitions}")
    print(f"acalvio query target option selectors: {acalvio_query_target_options.selectors}")

    return True