# 3-test_query_target_options.py

async def test_folder_enumeration_options(zerg_state=None):
    """Test SMTP Email folder enumeration by way of query target options"""
    print("Attempting to authenticate using SMTP Email connector")

    assert zerg_state, "this test requires valid zerg_state"

    smtp_server = zerg_state.get("smtp_server").get("value")
    smtp_port = zerg_state.get("smtp_port").get("value")
    imap_server = zerg_state.get("imap_server").get("value")
    imap_port = zerg_state.get("imap_port").get("value")
    email_username = zerg_state.get("email_username").get("value")
    email_password = zerg_state.get("email_password").get("value")

    from connectors.smtp_email.config import SMTPEmailConnectorConfig
    from connectors.smtp_email.connector import SMTPEmailConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = SMTPEmailConnectorConfig(
        smtp_server=smtp_server,
        smtp_port=int(smtp_port),
        imap_server=imap_server,
        imap_port=int(imap_port),
        username=email_username,
        password=email_password,
    )
    assert isinstance(config, ConnectorConfig), "SMTPEmailConnectorConfig should be of type ConnectorConfig"

    connector = SMTPEmailConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SMTPEmailConnectorConfig should be of type ConnectorConfig"

    smtp_email_query_target_options = await connector.get_query_target_options()
    assert isinstance(smtp_email_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert smtp_email_query_target_options, "Failed to retrieve query target options"

    print(f"smtp email query target option definitions: {smtp_email_query_target_options.definitions}")
    print(f"smtp email query target option selectors: {smtp_email_query_target_options.selectors}")

    return True