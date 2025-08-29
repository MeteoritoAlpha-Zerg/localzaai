# 5-test_error_events.py

async def test_error_events(zerg_state=None):
    """Test Sentry error event retrieval"""
    print("Testing Sentry error event retrieval")

    assert zerg_state, "this test requires valid zerg_state"

    sentry_api_token = zerg_state.get("sentry_api_token").get("value")
    sentry_organization_slug = zerg_state.get("sentry_organization_slug").get("value")
    sentry_base_url = zerg_state.get("sentry_base_url").get("value")

    from connectors.sentry.config import SentryConnectorConfig
    from connectors.sentry.connector import SentryConnector
    from connectors.sentry.target import SentryTarget
    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    config = SentryConnectorConfig(
        api_token=sentry_api_token,
        organization_slug=sentry_organization_slug,
        base_url=sentry_base_url
    )
    assert isinstance(config, ConnectorConfig), "SentryConnectorConfig should be of type ConnectorConfig"

    connector = SentryConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "SentryConnector should be of type Connector"

    sentry_query_target_options = await connector.get_query_target_options()
    assert isinstance(sentry_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    project_selector = None
    for selector in sentry_query_target_options.selectors:
        if selector.type == 'project_slugs':  
            project_selector = selector
            break

    assert project_selector, "failed to retrieve project selector from query target options"

    assert isinstance(project_selector.values, list), "project_selector values must be a list"
    project_slug = project_selector.values[0] if project_selector.values else None
    print(f"Selecting project slug: {project_slug}")

    assert project_slug, f"failed to retrieve project slug from project selector"

    target = SentryTarget(project_slugs=[project_slug])
    assert isinstance(target, ConnectorTargetInterface), "SentryTarget should be of type ConnectorTargetInterface"

    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    get_error_events_tool = next(tool for tool in tools if tool.name == "get_error_events")
    error_events_result = await get_error_events_tool.execute(project_slug=project_slug)
    error_events = error_events_result.result

    print("Type of returned error_events:", type(error_events))
    print(f"len events: {len(error_events)} events: {str(error_events)[:200]}")

    assert isinstance(error_events, list), "error_events should be a list"
    assert len(error_events) > 0, "error_events should not be empty"
    
    events_to_check = error_events[:3] if len(error_events) > 3 else error_events
    
    for event in events_to_check:
        assert isinstance(event, dict), "Each event should be a dictionary"
        assert "id" in event, "Each event should have an 'id' field"
        assert "title" in event, "Each event should have a 'title' field"
        assert "level" in event, "Each event should have a 'level' field"
        
        if "level" in event:
            valid_levels = ["debug", "info", "warning", "error", "fatal"]
            assert event["level"] in valid_levels, f"Event level should be valid"
        
        event_fields = ["dateCreated", "message", "platform", "user", "tags", "context"]
        present_fields = [field for field in event_fields if field in event]
        
        print(f"Event {event['id']} contains these fields: {', '.join(present_fields)}")
        
        if "dateCreated" in event:
            date_created = event["dateCreated"]
            assert isinstance(date_created, str), "Date created should be a string"
        
        if "user" in event and event["user"]:
            user = event["user"]
            assert isinstance(user, dict), "User should be a dictionary"
        
        if event == events_to_check[0]:
            print(f"Example event structure: {event}")

    print(f"Successfully retrieved and validated {len(error_events)} error events")

    return True