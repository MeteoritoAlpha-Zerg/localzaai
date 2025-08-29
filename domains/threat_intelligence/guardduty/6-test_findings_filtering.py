# 6-test_findings_filtering.py

# 6-test_findings_filtering.py

import datetime

async def test_findings_filtering(zerg_state=None):
    """Test filtering GuardDuty findings by severity and timestamp"""
    print("Attempting to authenticate using GuardDuty connector")

    assert zerg_state, "this test requires valid zerg_state"

    aws_region = zerg_state.get("aws_region").get("value")
    aws_access_key_id = zerg_state.get("aws_access_key_id").get("value")
    aws_secret_access_key = zerg_state.get("aws_secret_access_key").get("value")
    aws_session_token = zerg_state.get("aws_session_token").get("value")
    max_results = int(zerg_state.get("guardduty_findings_max_results").get("value"))

    from connectors.guardduty.config import GuardDutyConnectorConfig
    from connectors.guardduty.connector import GuardDutyConnector
    from connectors.guardduty.target import GuardDutyTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = GuardDutyConnectorConfig(
        region=aws_region,
        access_key_id=aws_access_key_id,
        secret_access_key=aws_secret_access_key,
        session_token=aws_session_token
    )
    assert isinstance(config, ConnectorConfig), "GuardDutyConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = GuardDutyConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "GuardDutyConnector should be of type Connector"

    # get query target options
    guardduty_query_target_options = await connector.get_query_target_options()
    assert isinstance(guardduty_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select detectors to target
    detector_selector = None
    for selector in guardduty_query_target_options.selectors:
        if selector.type == 'detectors':  
            detector_selector = selector
            break

    assert detector_selector, "failed to retrieve detector selector from query target options"

    assert isinstance(detector_selector.values, list), "detector_selector values must be a list"
    detector_id = detector_selector.values[0] if detector_selector.values else None
    print(f"Selecting detector ID: {detector_id}")

    assert detector_id, f"failed to retrieve detector ID from detector selector"

    # set up the target with detector IDs
    target = GuardDutyTarget(detectors=[detector_id])
    assert isinstance(target, ConnectorTargetInterface), "GuardDutyTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"
    
    # Get the filter guardduty findings tool
    get_guardduty_findings_tool = next(tool for tool in tools if tool.name == "get_guardduty_findings")
    
    ##### Test 1: Filter by HIGH severity #####
    print("\n--- Testing filtering by HIGH severity ---")
    high_severity_result = await get_guardduty_findings_tool.execute(
        detector_id=detector_id,
        severity_level="HIGH",
        max_results=max_results
    )
    high_severity_findings = high_severity_result.raw_result
    
    print(f"Found {len(high_severity_findings)} HIGH severity findings")
    
    # Verify all findings have HIGH severity
    if high_severity_findings:
        for finding in high_severity_findings:
            assert finding["severity"] >= 7.0, f"Finding {finding['id']} has severity {finding['severity']}, expected 7.0 or higher for HIGH severity"
    
    ##### Test 2: Filter by MEDIUM severity #####
    print("\n--- Testing filtering by MEDIUM severity ---")
    medium_severity_result = await get_guardduty_findings_tool.execute(
        detector_id=detector_id,
        severity_level="MEDIUM",
        max_results=max_results
    )
    medium_severity_findings = medium_severity_result.raw_result
    
    print(f"Found {len(medium_severity_findings)} MEDIUM severity findings")
    
    # Verify all findings have MEDIUM severity
    if medium_severity_findings:
        for finding in medium_severity_findings:
            assert 4.0 <= finding["severity"] < 7.0, f"Finding {finding['id']} has severity {finding['severity']}, expected between 4.0 and 7.0 for MEDIUM severity"
    
    ##### Test 3: Filter by LOW severity #####
    print("\n--- Testing filtering by LOW severity ---")
    low_severity_result = await get_guardduty_findings_tool.execute(
        detector_id=detector_id,
        severity_level="LOW",
        max_results=max_results
    )
    low_severity_findings = low_severity_result.raw_result
    
    print(f"Found {len(low_severity_findings)} LOW severity findings")
    
    # Verify all findings have LOW severity
    if low_severity_findings:
        for finding in low_severity_findings:
            assert finding["severity"] < 4.0, f"Finding {finding['id']} has severity {finding['severity']}, expected less than 4.0 for LOW severity"
    
    ##### Test 4: Filter by time range - last 7 days #####
    print("\n--- Testing filtering by time range (last 7 days) ---")
    now = datetime.datetime.now()
    seven_days_ago = now - datetime.timedelta(days=7)
    
    # Format timestamps in ISO format
    start_time = seven_days_ago.isoformat()
    end_time = now.isoformat()
    
    time_filtered_result = await get_guardduty_findings_tool.execute(
        detector_id=detector_id,
        start_time=start_time,
        end_time=end_time,
        max_results=max_results
    )
    time_filtered_findings = time_filtered_result.raw_result
    
    print(f"Found {len(time_filtered_findings)} findings from the last 7 days")
    
    # Verify all findings are within the time range
    if time_filtered_findings:
        for finding in time_filtered_findings:
            finding_created_at = datetime.datetime.fromisoformat(finding["createdAt"].replace('Z', '+00:00'))
            assert seven_days_ago <= finding_created_at <= now, \
                f"Finding {finding['id']} was created at {finding_created_at}, which is outside the requested time range"
    
    ##### Test 5: Test pagination #####
    print("\n--- Testing pagination of findings ---")
    
    # Set a small page size to test pagination
    page_size = min(5, max_results)
    
    # First page
    first_page_result = await get_guardduty_findings_tool.execute(
        detector_id=detector_id,
        max_results=page_size
    )
    first_page_findings = first_page_result.raw_result
    
    print(f"First page returned {len(first_page_findings)} findings")
    
    # Check if there are enough findings to test pagination
    if len(first_page_findings) == page_size and hasattr(first_page_result, 'next_token') and first_page_result.next_token:
        next_token = first_page_result.next_token
        
        # Second page
        second_page_result = await get_guardduty_findings_tool.execute(
            detector_id=detector_id,
            max_results=page_size,
            next_token=next_token
        )
        second_page_findings = second_page_result.raw_result
        
        print(f"Second page returned {len(second_page_findings)} findings")
        
        # Verify second page contains different findings
        first_page_ids = {finding["id"] for finding in first_page_findings}
        second_page_ids = {finding["id"] for finding in second_page_findings}
        
        assert not first_page_ids.intersection(second_page_ids), "Second page contains findings from the first page"
        
        print("Pagination is working correctly")
    else:
        print("Not enough findings to fully test pagination, but the pagination mechanism is in place")
    
    ##### Test 6: Combined filters - HIGH severity in last 24 hours #####
    print("\n--- Testing combined filtering (HIGH severity in last 24 hours) ---")
    one_day_ago = now - datetime.timedelta(days=1)
    start_time_24h = one_day_ago.isoformat()
    
    combined_filter_result = await get_guardduty_findings_tool.execute(
        detector_id=detector_id,
        severity_level="HIGH",
        start_time=start_time_24h,
        end_time=end_time,
        max_results=max_results
    )
    combined_filter_findings = combined_filter_result.raw_result
    
    print(f"Found {len(combined_filter_findings)} HIGH severity findings from the last 24 hours")
    
    # Verify all findings match both criteria
    if combined_filter_findings:
        for finding in combined_filter_findings:
            finding_created_at = datetime.datetime.fromisoformat(finding["createdAt"].replace('Z', '+00:00'))
            assert finding["severity"] >= 7.0, \
                f"Finding {finding['id']} has severity {finding['severity']}, expected 7.0 or higher for HIGH severity"
            assert one_day_ago <= finding_created_at <= now, \
                f"Finding {finding['id']} was created at {finding_created_at}, which is outside the requested time range"
    
    print("\nAll filtering tests completed successfully")
    
    return True