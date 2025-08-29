async def test_table_enumeration_options(zerg_state=None):
    """Test ServiceNow table enumeration by way of query target options"""
    print("Attempting to authenticate using ServiceNow connector")

    assert zerg_state, "this test requires valid zerg_state"

    servicenow_instance_url = zerg_state.get("servicenow_instance_url").get("value")
    servicenow_client_id = zerg_state.get("servicenow_client_id").get("value")
    servicenow_client_secret = zerg_state.get("servicenow_client_secret").get("value")

    from connectors.servicenow.config import ServiceNowConnectorConfig
    from connectors.servicenow.connector import ServiceNowConnector
    from connectors.servicenow.target import ServiceNowTarget

    config = ServiceNowConnectorConfig(
        instance_url=servicenow_instance_url,
        client_id=servicenow_client_id,
        client_secret=SecretStr(servicenow_client_secret)
    )
    connector = ServiceNowConnector(config)

    connector_target = ServiceNowTarget(config=config)

    servicenow_query_target_options = await connector.get_query_target_options()

    assert servicenow_query_target_options, "Failed to retrieve query target options"

    def truncate_str(s, max_length=200):
        s = str(s)
        return s[:max_length] + ("..." if len(s) > max_length else "")

    print(f"servicenow query target option definitions: {truncate_str(servicenow_query_target_options.definitions)}")
    print(f"servicenow query target option selectors: {truncate_str(servicenow_query_target_options.selectors)}")

    return True