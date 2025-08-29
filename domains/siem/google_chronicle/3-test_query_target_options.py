# 3-test_query_target_options.py

async def test_data_source_enumeration_options(zerg_state=None):
    """Test Google Chronicle data source enumeration by way of query target options"""
    print("Attempting to authenticate using Google Chronicle connector")

    assert zerg_state, "this test requires valid zerg_state"

    chronicle_service_account_path = zerg_state.get("chronicle_service_account_path").get("value")
    chronicle_customer_id = zerg_state.get("chronicle_customer_id").get("value")

    from connectors.chronicle.config import ChronicleConnectorConfig
    from connectors.chronicle.connector import ChronicleConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = ChronicleConnectorConfig(
        service_account_path=chronicle_service_account_path,
        customer_id=chronicle_customer_id,
    )
    assert isinstance(config, ConnectorConfig), "ChronicleConnectorConfig should be of type ConnectorConfig"

    connector = ChronicleConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ChronicleConnector should be of type Connector"

    chronicle_query_target_options = await connector.get_query_target_options()
    assert isinstance(chronicle_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert chronicle_query_target_options, "Failed to retrieve query target options"

    print(f"Google Chronicle query target option definitions: {chronicle_query_target_options.definitions}")
    print(f"Google Chronicle query target option selectors: {chronicle_query_target_options.selectors}")

    return True