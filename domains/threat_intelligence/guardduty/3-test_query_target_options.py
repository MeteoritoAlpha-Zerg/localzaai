# 3-test_query_target_options.py

async def test_project_enumeration_options(zerg_state=None):
    """Test GuardDuty project enumeration by way of query target options"""
    print("Attempting to authenticate using GuardDuty connector")

    assert zerg_state, "this test requires valid zerg_state"

    aws_region = zerg_state.get("aws_region").get("value")
    aws_access_key_id = zerg_state.get("aws_access_key_id").get("value")
    aws_secret_access_key = zerg_state.get("aws_secret_access_key").get("value")
    aws_session_token = zerg_state.get("aws_session_token").get("value")

    from connectors.guardduty.config import GuarddutyConnectorConfig
    from connectors.guardduty.connector import GuarddutyConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    # initialize the connector config
    config = GuarddutyConnectorConfig(
        aws_region=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
    )
    assert isinstance(config, ConnectorConfig), "GuarddutyConnectorConfig should be of type ConnectorConfig"

    # initialize the connector
    connector = GuarddutyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GuarddutyConnector should be of type Connector"

    query_target_options = await connector.get_query_target_options()
    assert isinstance(query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert query_target_options, "Failed to retrieve query target options"

    print(f"guardduty query target option definitions: {query_target_options.definitions}")
    print(f"guardduty query target option selectors: {query_target_options.selectors}")

    return True

