# 3-test_query_target_options.py

async def test_data_source_enumeration_options(zerg_state=None):
    """Test RSA Archer data source enumeration by way of query target options"""
    print("Attempting to connect to RSA Archer APIs using RSA Archer connector")

    assert zerg_state, "this test requires valid zerg_state"

    rsa_archer_api_url = zerg_state.get("rsa_archer_api_url").get("value")
    rsa_archer_username = zerg_state.get("rsa_archer_username").get("value")
    rsa_archer_password = zerg_state.get("rsa_archer_password").get("value")
    rsa_archer_instance_name = zerg_state.get("rsa_archer_instance_name").get("value")

    from connectors.rsa_archer.config import RSAArcherConnectorConfig
    from connectors.rsa_archer.connector import RSAArcherConnector

    from connectors.config import ConnectorConfig
    from connectors.query_target_options import ConnectorQueryTargetOptions
    from connectors.connector import Connector

    config = RSAArcherConnectorConfig(
        api_url=rsa_archer_api_url,
        username=rsa_archer_username,
        password=rsa_archer_password,
        instance_name=rsa_archer_instance_name,
    )
    assert isinstance(config, ConnectorConfig), "RSAArcherConnectorConfig should be of type ConnectorConfig"

    connector = RSAArcherConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "RSAArcherConnector should be of type Connector"

    rsa_archer_query_target_options = await connector.get_query_target_options()
    assert isinstance(rsa_archer_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    assert rsa_archer_query_target_options, "Failed to retrieve query target options"

    print(f"RSA Archer query target option definitions: {rsa_archer_query_target_options.definitions}")
    print(f"RSA Archer query target option selectors: {rsa_archer_query_target_options.selectors}")

    # Verify that applications are available as data sources
    application_selector = None
    for selector in rsa_archer_query_target_options.selectors:
        if selector.type == 'applications':
            application_selector = selector
            break

    assert application_selector, "Failed to find applications selector in query target options"
    assert isinstance(application_selector.values, list), "application_selector values must be a list"
    assert len(application_selector.values) > 0, "application_selector should have available applications"

    # Verify expected application types are present (common RSA Archer applications)
    expected_apps = ["incident", "risk", "control", "compliance"]
    available_apps = application_selector.values
    
    # Check if at least one expected application type is present
    found_apps = []
    for expected in expected_apps:
        app_found = any(expected.lower() in app.lower() for app in available_apps)
        if app_found:
            found_apps.append(expected)
    
    assert len(found_apps) > 0, f"No expected application types found. Available: {available_apps}, Expected: {expected_apps}"
    print(f"Found expected applications: {found_apps}")

    return True