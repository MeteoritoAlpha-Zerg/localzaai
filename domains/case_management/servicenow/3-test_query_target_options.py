# 3-test_query_target_options.py

async def test_query_target_options(zerg_state=None):
    """Test ServiceNow enumeration by way of query target options"""
    print("Attempting to authenticate using ServiceNow connector")

    assert zerg_state, "this test requires valid zerg_state"

    servicenow_instance_url = zerg_state.get("servicenow_instance_url").get("value")
    servicenow_client_id = zerg_state.get("servicenow_client_id").get("value")
    servicenow_client_secret = zerg_state.get("servicenow_client_secret").get("value")
    servicenow_username = zerg_state.get("servicenow_username").get("value")
    servicenow_password = zerg_state.get("servicenow_username").get("value")

    from connectors.servicenow.config import ServiceNowConnectorConfig
    from connectors.servicenow.connector import ServiceNowConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = ServiceNowConnectorConfig(
        instance_url=servicenow_instance_url,
        client_id=servicenow_client_id,
        client_secret=servicenow_client_secret,
        servicenow_username=servicenow_username,
        servicenow_password=servicenow_password
    )
    assert isinstance(config, ConnectorConfig), "ServiceNowConnectorConfig should be of type ConnectorConfig"

    connector = ServiceNowConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ServiceNowConnector should be of type Connector"

    servicenow_query_target_options = await connector.get_query_target_options()
    assert isinstance(servicenow_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert servicenow_query_target_options, "Failed to retrieve query target options"

    print(f"servicenow query target option definitions: {servicenow_query_target_options.definitions}")
    print(f"servicenow query target option selectors: {servicenow_query_target_options.selectors}")

    return True