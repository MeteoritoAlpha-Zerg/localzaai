# 5-test_get_alerts.py

async def test_get_alerts(zerg_state=None):
    """Test CISA alerts and advisories retrieval"""
    print("Testing CISA alerts and advisories retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    cisa_base_url = zerg_state.get("cisa_base_url").get("value")
    cisa_kev_url = zerg_state.get("cisa_kev_url").get("value")

    from connectors.cisa.config import CISAConnectorConfig
    from connectors.cisa.connector import CISAConnector
    from connectors.cisa.target import CISATarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = CISAConnectorConfig(
        base_url=cisa_base_url,
        kev_url=cisa_kev_url
    )
    assert isinstance(config, ConnectorConfig), "CISAConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CISAConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CISAConnector should be of type Connector"

    # get query target options
    cisa_query_target_options = await connector.get_query_target_options()
    assert isinstance(cisa_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select alerts data source
    data_source_selector = None
    for selector in cisa_query_target_options.selectors:
        if selector.type == 'data_sources':  
            data_source_selector = selector
            break

    assert data_source_selector, "failed to retrieve data source selector from query target options"
    assert isinstance(data_source_selector.values, list), "data_source_selector values must be a list"
    
    # Find alerts in available data sources
    alerts_source = None
    for source in data_source_selector.values:
        if 'alert' in source.lower() or 'advisory' in source.lower():
            alerts_source = source
            break
    
    assert alerts_source, "Alerts data source not found in available options"
    print(f"Selecting alerts data source: {alerts_source}")

    # set up the target with alerts data source
    target = CISATarget(data_sources=[alerts_source])
    assert isinstance(target, ConnectorTargetInterface), "CISATarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the get_cisa_alerts tool and execute it
    get_cisa_alerts_tool = next(tool for tool in tools if tool.name == "get_cisa_alerts")
    alerts_result = await get_cisa_alerts_tool.execute()
    alerts_data = alerts_result.result

    print("Type of returned alerts data:", type(alerts_data))
    print(f"Alerts count: {len(alerts_data)} sample: {str(alerts_data)[:200]}")

    # Verify that alerts_data is a list
    assert isinstance(alerts_data, list), "Alerts data should be a list"
    assert len(alerts_data) > 0, "Alerts data should not be empty"
    
    # Limit the number of alerts to check if there are many
    alerts_to_check = alerts_data[:3] if len(alerts_data) > 3 else alerts_data
    
    # Verify structure of each alert entry
    for alert in alerts_to_check:
        # Verify essential alert fields
        assert "id" in alert, "Each alert should have an 'id' field"
        assert "title" in alert, "Each alert should have a 'title' field"
        assert "published" in alert, "Each alert should have a 'published' field"
        
        # Check for additional common fields
        common_fields = ["description", "severity", "type", "url"]
        present_fields = [field for field in common_fields if field in alert]
        
        print(f"Alert {alert['id']} contains these fields: {', '.join(present_fields)}")
        
        # Verify title is not empty
        assert alert["title"].strip(), "Alert title should not be empty"
        
        # Verify published date format (should be a date string)
        assert alert["published"], "Published date should not be empty"
        
        # Log the structure of the first alert for debugging
        if alert == alerts_to_check[0]:
            print(f"Example alert structure: {alert}")

    print(f"Successfully retrieved and validated {len(alerts_data)} CISA alerts")

    return True