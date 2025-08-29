# 2-test_connector_check_connection.py

async def test_connector_check_connection(zerg_state=None):
    """Test whether connector returns a valid connection check"""
    print("Testing smtp email connector connection")

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

    # initialize the connector
    connector = SMTPEmailConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SMTPEmailConnector should be of type Connector"

    connection_valid = await connector.check_connection()

    if not isinstance(connection_valid, bool) or not connection_valid:
        raise Exception("check_connection did not return True")

    return True