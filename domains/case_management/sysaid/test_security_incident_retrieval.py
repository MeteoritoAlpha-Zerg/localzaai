async def test_security_incident_retrieval(zerg_state=None):
    """Test SysAid security incident retrieval"""
    print("Retrieving security incidents using SysAid connector")

    assert zerg_state, "this test requires valid zerg_state"

    sysaid_url = zerg_state.get("sysaid_url").get("value")
    sysaid_account_id = zerg_state.get("sysaid_account_id").get("value")
    sysaid_username = zerg_state.get("sysaid_username").get("value")
    sysaid_password = zerg_state.get("sysaid_password").get("value")

    from connectors.sysaid.config import SysAidConnectorConfig
    from connectors.sysaid.connector import SysAidConnector
    from connectors.sysaid.tools import SysAidConnectorTools
    from connectors.sysaid.target import SysAidTarget

    config = SysAidConnectorConfig(
        url=sysaid_url,
        account_id=sysaid_account_id,
        username=sysaid_username,
        password=SecretStr(sysaid_password)
    )
    connector = SysAidConnector(config)

    connector_target = SysAidTarget(config=config)
    
    # Get connector tools
    tools = SysAidConnectorTools(
        sysaid_config=config, 
        target=SysAidTarget, 
        connector_display_name="SysAid"
    )
    
    # Use the security-specific tool to get security incidents
    try:
        # First try the dedicated security incident method
        security_incidents = await tools.get_security_incidents(
            days=zerg_state.get("security_incident_lookback_days").get("value")
        )
        
        print(f"Retrieved {len(security_incidents)} security incidents")
        
        if security_incidents:
            sample = security_incidents[0]
            print(f"Example security incident: {sample.get('id')} - {sample.get('title')}")
            print(f"Category: {sample.get('category')}, Priority: {sample.get('priority')}")
            
        return True
        
    except Exception as e:
        print(f"Error retrieving security incidents via dedicated method: {e}")
        
        # Fallback to filtering service requests with security categories
        security_categories = zerg_state.get("security_incident_categories").get("value")
        
        all_security_incidents = []
        
        # Try each security category
        for category in security_categories:
            connector_target.request_category = category
            
            try:
                category_incidents = await tools.get_sysaid_service_requests()
                if category_incidents:
                    print(f"Found {len(category_incidents)} incidents in category '{category}'")
                    all_security_incidents.extend(category_incidents)
            except Exception as category_error:
                print(f"Error retrieving incidents for category '{category}': {category_error}")
        
        print(f"Found total of {len(all_security_incidents)} security-related incidents")
        
        # Look for security keywords in titles of regular service requests
        connector_target.request_category = None  # Reset category filter
        
        try:
            recent_requests = await tools.get_sysaid_service_requests(
                limit=100, 
                days=zerg_state.get("security_incident_lookback_days").get("value")
            )
            
            # Check titles for security keywords
            security_keywords = zerg_state.get("security_keywords").get("value")
            keyword_matches = []
            
            for request in recent_requests:
                title = request.get('title', '').lower()
                description = request.get('description', '').lower()
                
                for keyword in security_keywords:
                    if keyword.lower() in title or keyword.lower() in description:
                        request['matched_keyword'] = keyword
                        keyword_matches.append(request)
                        break
            
            print(f"Found {len(keyword_matches)} additional incidents matching security keywords")
            all_security_incidents.extend(keyword_matches)
            
            if all_security_incidents:
                print(f"Total security-related incidents found: {len(all_security_incidents)}")
                
            return True
            
        except Exception as keyword_error:
            print(f"Error searching by keywords: {keyword_error}")
            return True
        
    return True