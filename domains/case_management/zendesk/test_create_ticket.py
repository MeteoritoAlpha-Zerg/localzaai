async def test_create_ticket(zerg_state=None):
    """Test Zendesk ticket creation"""
    print("Attempting to create a ticket using Zendesk connector")

    assert zerg_state, "this test requires valid zerg_state"

    zendesk_subdomain = zerg_state.get("zendesk_subdomain").get("value")
    zendesk_email = zerg_state.get("zendesk_email").get("value")
    zendesk_api_token = zerg_state.get("zendesk_api_token").get("value")

    from connectors.zendesk.config import ZendeskConnectorConfig
    from connectors.zendesk.connector import ZendeskConnector
    from connectors.zendesk.tools import ZendeskConnectorTools
    from connectors.zendesk.target import ZendeskTarget

    config = ZendeskConnectorConfig(
        subdomain=zendesk_subdomain,
        email=zendesk_email,
        api_token=SecretStr(zendesk_api_token)
    )
    connector = ZendeskConnector(config)

    connector_target = ZendeskTarget(config=config)
    
    # Get connector tools
    tools = ZendeskConnectorTools(
        zendesk_config=config, 
        target=ZendeskTarget, 
        connector_display_name="Zendesk"
    )
    
    # Create a test ticket with a unique subject
    import time
    timestamp = int(time.time())
    ticket_subject = f"Test Ticket - {timestamp}"
    ticket_description = "This is a test ticket created by the Zendesk connector test"
    
    # Optional additional fields
    ticket_type = "question"  # Can be "problem", "incident", "question" or "task"
    ticket_priority = "normal"  # Can be "low", "normal", "high", "urgent"
    
    new_ticket = await tools.create_zendesk_ticket(
        subject=ticket_subject,
        description=ticket_description,
        type=ticket_type,
        priority=ticket_priority
    )
    
    assert new_ticket, "Failed to create new ticket"
    assert new_ticket.get('id'), "New ticket does not have an ID"
    assert new_ticket.get('subject') == ticket_subject, "New ticket subject does not match requested subject"
    
    ticket_id = new_ticket.get('id')
    print(f"Successfully created ticket #{ticket_id} with subject '{ticket_subject}'")
    
    # Store the ticket ID for later cleanup or reference
    # This would be implemented in a real test environment
    
    return True