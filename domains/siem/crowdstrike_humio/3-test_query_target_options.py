# 3-test_query_target_options.py

async def test_repository_data_source_enumeration_options(zerg_state=None):
    """Test CrowdStrike Humio repository and data source enumeration by way of query target options"""
    print("Attempting to authenticate using CrowdStrike Humio connector")

    assert zerg_state, "this test requires valid zerg_state"

    humio_api_token = zerg_state.get("humio_api_token").get("value")
    humio_base_url = zerg_state.get("humio_base_url").get("value")
    humio_organization = zerg_state.get("humio_organization").get("value")

    from connectors.crowdstrike_humio.config import CrowdStrikeHumioConnectorConfig
    from connectors.crowdstrike_humio.connector import CrowdStrikeHumioConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = CrowdStrikeHumioConnectorConfig(
        api_token=humio_api_token,
        base_url=humio_base_url,
        organization=humio_organization,
    )
    assert isinstance(config, ConnectorConfig), "CrowdStrikeHumioConnectorConfig should be of type ConnectorConfig"

    connector = CrowdStrikeHumioConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CrowdStrikeHumioConnector should be of type Connector"

    humio_query_target_options = await connector.get_query_target_options()
    assert isinstance(humio_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert humio_query_target_options, "Failed to retrieve query target options"

    print(f"CrowdStrike Humio query target option definitions: {humio_query_target_options.definitions}")
    print(f"CrowdStrike Humio query target option selectors: {humio_query_target_options.selectors}")

    return True