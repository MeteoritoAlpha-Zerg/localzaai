# 3-test_query_target_options.py

async def test_domain_list_monitoring_enumeration_options(zerg_state=None):
    """Test DomainTools domain list and monitoring profile enumeration by way of query target options"""
    print("Attempting to authenticate using DomainTools connector")

    assert zerg_state, "this test requires valid zerg_state"

    domaintools_api_username = zerg_state.get("domaintools_api_username").get("value")
    domaintools_api_key = zerg_state.get("domaintools_api_key").get("value")
    domaintools_base_url = zerg_state.get("domaintools_base_url").get("value")

    from connectors.domaintools.config import DomainToolsConnectorConfig
    from connectors.domaintools.connector import DomainToolsConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = DomainToolsConnectorConfig(
        api_username=domaintools_api_username,
        api_key=domaintools_api_key,
        base_url=domaintools_base_url,
    )
    assert isinstance(config, ConnectorConfig), "DomainToolsConnectorConfig should be of type ConnectorConfig"

    connector = DomainToolsConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "DomainToolsConnector should be of type Connector"

    domaintools_query_target_options = await connector.get_query_target_options()
    assert isinstance(domaintools_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert domaintools_query_target_options, "Failed to retrieve query target options"

    print(f"DomainTools query target option definitions: {domaintools_query_target_options.definitions}")
    print(f"DomainTools query target option selectors: {domaintools_query_target_options.selectors}")

    return True