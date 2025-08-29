# 3-test_query_target_options.py

async def test_project_enumeration_options(zerg_state=None):
    """Test Proofpoint project enumeration by way of query target options"""
    print("Attempting to authenticate using Proofpoint connector")

    assert zerg_state, "this test requires valid zerg_state"

    proofpoint_api_host = zerg_state.get("proofpoint_api_host").get("value")
    proofpoint_principal = zerg_state.get("proofpoint_principal").get("value")
    proofpoint_secret = zerg_state.get("proofpoint_secret").get("value")

    from connectors.proofpoint.config import ProofpointConnectorConfig
    from connectors.proofpoint.connector import ProofpointConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    # Note this is common code
    from common.models.tool import Tool

    # initialize the connector config
    config = ProofpointConnectorConfig(
        api_host=proofpoint_api_host,
        principal=proofpoint_principal,
        secret=proofpoint_secret,
    )
    assert isinstance(config, ConnectorConfig), "ProofpointConnectorConfig should be of type ConnectorConfig"

    connector = ProofpointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ProofpointConnectorConfig should be of type ConnectorConfig"

    proofpoint_query_target_options = await connector.get_query_target_options()
    assert isinstance(proofpoint_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert proofpoint_query_target_options, "Failed to retrieve query target options"

    print(f"proofpoint query target option definitions: {proofpoint_query_target_options.definitions}")
    print(f"proofpoint query target option selectors: {proofpoint_query_target_options.selectors}")

    return True