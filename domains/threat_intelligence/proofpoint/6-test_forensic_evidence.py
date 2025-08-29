# 6-test_forensic_evidence.py

async def test_forensic_evidence_retrieval(zerg_state=None):
    """Test Proofpoint forensic evidence retrieval using the Forensics API"""
    print("Attempting to authenticate using Proofpoint connector")

    assert zerg_state, "this test requires valid zerg_state"

    proofpoint_api_host = zerg_state.get("proofpoint_api_host").get("value")
    proofpoint_principal = zerg_state.get("proofpoint_principal").get("value")
    proofpoint_secret = zerg_state.get("proofpoint_secret").get("value")

    from connectors.proofpoint.config import ProofpointConnectorConfig
    from connectors.proofpoint.connector import ProofpointConnector
    from connectors.proofpoint.target import ProofpointTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = ProofpointConnectorConfig(
        api_host=proofpoint_api_host,
        principal=proofpoint_principal,
        secret=proofpoint_secret
    )
    assert isinstance(config, ConnectorConfig), "ProofpointConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = ProofpointConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "ProofpointConnector should be of type Connector"

    # get query target options
    proofpoint_query_target_options = await connector.get_query_target_options()
    assert isinstance(proofpoint_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # set up the target
    target = ProofpointTarget()
    assert isinstance(target, ConnectorTargetInterface), "ProofpointTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(target=target)
    assert isinstance(tools, list), "Tools response is not a list"

    # Find a valid threat ID for testing
    # In a real test, you might want to:
    # 1. Use a known test threat ID
    # 2. First query for threats and then use one of the IDs
    # 3. Have a mock API that returns consistent test data
    # For this example, we'll use a placeholder - in actual implementation you'd need a real threat ID
    test_threat_id = "sample_threat_id"  # Replace with an actual threat ID for testing
    
    # grab the get_forensic_evidence tool and execute it with threat ID
    get_forensic_evidence_tool = next((tool for tool in tools if tool.name == "get_forensic_evidence"), None)
    assert get_forensic_evidence_tool is not None, "get_forensic_evidence tool not found"
    
    forensic_evidence_result = await get_forensic_evidence_tool.execute(
        threat_id=test_threat_id,
        include_campaign_forensics=False  # By default, just get forensics for the specific threat
    )
    forensic_evidence = forensic_evidence_result.raw_result

    print("Type of returned forensic_evidence:", type(forensic_evidence))
    print(f"Forensic evidence: {str(forensic_evidence)[:200]}...")

    # Verify that forensic_evidence follows the expected format from the API documentation
    assert isinstance(forensic_evidence, dict), "forensic_evidence should be a dict"
    
    # Check essential top-level fields
    assert "generated" in forensic_evidence, "Missing 'generated' timestamp field"
    assert "reports" in forensic_evidence, "Missing 'reports' field"
    assert isinstance(forensic_evidence["reports"], list), "'reports' should be a list"
    
    # If reports are available, verify the structure of the first report
    if forensic_evidence["reports"]:
        report = forensic_evidence["reports"][0]
        
        # Check essential report fields
        essential_report_fields = ["name", "scope", "type", "id", "forensics"]
        for field in essential_report_fields:
            assert field in report, f"Report missing essential field: {field}"
        
        # Verify report scope validity
        assert report["scope"] in ["campaign", "threat"], "Report scope should be 'campaign' or 'threat'"
        
        # Verify report type validity
        assert report["type"] in ["attachment", "url", "hybrid"], f"Report type should be one of: attachment, url, hybrid"
        
        # Verify forensics is a list
        assert isinstance(report["forensics"], list), "report['forensics'] should be a list"
        
        # If forensic evidence is available, verify the structure of the first evidence
        if report["forensics"]:
            evidence = report["forensics"][0]
            
            # Check essential evidence fields
            essential_evidence_fields = ["type", "display", "malicious", "what", "platforms"]
            for field in essential_evidence_fields:
                assert field in evidence, f"Evidence missing essential field: {field}"
            
            # Verify "what" is a dictionary containing evidence-specific data
            assert isinstance(evidence["what"], dict), "evidence['what'] should be a dictionary"
            
            # Verify platforms is a list
            assert isinstance(evidence["platforms"], list), "evidence['platforms'] should be a list"
            
            # If platforms are available, verify the structure of the first platform
            if evidence["platforms"]:
                platform = evidence["platforms"][0]
                
                # Check essential platform fields
                essential_platform_fields = ["name", "os", "version"]
                for field in essential_platform_fields:
                    assert field in platform, f"Platform missing essential field: {field}"
    
    # Optional: Test campaign forensics if threat is associated with a campaign
    # This requires knowing in advance that the threat is part of a campaign
    try:
        campaign_forensic_evidence_result = await get_forensic_evidence_tool.execute(
            threat_id=test_threat_id,
            include_campaign_forensics=True
        )
        campaign_forensic_evidence = campaign_forensic_evidence_result.raw_result
        
        print("Successfully retrieved campaign forensic evidence")
        print(f"Number of reports in campaign forensics: {len(campaign_forensic_evidence.get('reports', []))}")
    except Exception as e:
        print(f"Campaign forensics retrieval failed or threat not associated with campaign: {e}")
    
    # Print a summary of the evidence types found
    if forensic_evidence["reports"] and forensic_evidence["reports"][0]["forensics"]:
        evidence_types = set(evidence["type"] for evidence in forensic_evidence["reports"][0]["forensics"])
        print(f"Evidence types found: {', '.join(evidence_types)}")
        
        # Print details about one evidence of each type
        for evidence_type in evidence_types:
            evidence = next((e for e in forensic_evidence["reports"][0]["forensics"] if e["type"] == evidence_type), None)
            if evidence:
                print(f"\nEvidence type: {evidence_type}")
                print(f"Display: {evidence.get('display', 'N/A')}")
                print(f"Malicious: {evidence.get('malicious', 'N/A')}")
                
                # Print platforms
                if evidence.get("platforms"):
                    platforms = [f"{p.get('name', 'Unknown')} ({p.get('os', 'Unknown')} {p.get('version', 'Unknown')})" 
                               for p in evidence.get("platforms", [])]
                    print(f"Platforms: {', '.join(platforms[:3])}" + 
                          (f" and {len(platforms) - 3} more..." if len(platforms) > 3 else ""))

    print(f"Successfully retrieved and validated forensic evidence for threat ID: {test_threat_id}")

    return True