# 7-test_certificate_search.py

async def test_certificate_search(zerg_state=None):
    """Test Censys certificate search by way of connector tools"""
    print("Attempting to authenticate using Censys connector")

    assert zerg_state, "this test requires valid zerg_state"

    censys_api_id = zerg_state.get("censys_api_id").get("value")
    censys_api_secret = zerg_state.get("censys_api_secret").get("value")
    censys_base_url = zerg_state.get("censys_base_url").get("value")

    from connectors.censys.config import CensysConnectorConfig
    from connectors.censys.connector import CensysConnector
    from connectors.censys.tools import CensysConnectorTools, SearchCertificatesInput
    from connectors.censys.target import CensysTarget

    from connectors.config import ConnectorConfig
    from connectors.connector import Connector, ConnectorTargetInterface
    from connectors.query_target_options import ConnectorQueryTargetOptions

    # set up the config
    config = CensysConnectorConfig(
        api_id=censys_api_id,
        api_secret=censys_api_secret,
        base_url=censys_base_url
    )
    assert isinstance(config, ConnectorConfig), "CensysConnectorConfig should be of type ConnectorConfig"

    # set up the connector
    connector = CensysConnector
    await connector.initialize(
        config=config,
        user_id="test_user_id",
        encryption_key="test_enc_key"
    )
    assert isinstance(connector, Connector), "CensysConnector should be of type Connector"

    # get query target options
    censys_query_target_options = await connector.get_query_target_options()
    assert isinstance(censys_query_target_options, ConnectorQueryTargetOptions), "query target options should be of type ConnectorQueryTargetOptions"

    # select search indices to target
    index_selector = None
    for selector in censys_query_target_options.selectors:
        if selector.type == 'search_indices':  
            index_selector = selector
            break

    assert index_selector, "failed to retrieve search index selector from query target options"

    assert isinstance(index_selector.values, list), "index_selector values must be a list"
    search_index = "certificates"  # Default to certificates index for this test
    
    # Verify certificates index is available
    assert search_index in index_selector.values, f"certificates index not available in search indices: {index_selector.values}"
    
    print(f"Selecting search index: {search_index}")

    # set up the target with search indices
    target = CensysTarget(search_indices=[search_index])
    assert isinstance(target, ConnectorTargetInterface), "CensysTarget should be of type ConnectorTargetInterface"

    # get tools
    tools = await connector.get_tools(
        target=target
    )
    assert isinstance(tools, list), "Tools response is not a list"

    # grab the search_censys_certificates tool and execute it with a basic query
    search_certificates_tool = next(tool for tool in tools if tool.name == "search_censys_certificates")
    
    # Use a basic search query that should return certificate results
    search_query = "names: *.google.com"
    certificates_result = await search_certificates_tool.execute(query=search_query, per_page=10)
    censys_certificates = certificates_result.result

    print("Type of returned censys_certificates:", type(censys_certificates))
    print(f"len certificates: {len(censys_certificates)} certificates: {str(censys_certificates)[:200]}")

    # Verify that censys_certificates is a list
    assert isinstance(censys_certificates, list), "censys_certificates should be a list"
    assert len(censys_certificates) > 0, "censys_certificates should not be empty"
    
    # Limit the number of certificates to check if there are many
    certificates_to_check = censys_certificates[:5] if len(censys_certificates) > 5 else censys_certificates
    
    # Verify structure of each certificate object
    for certificate in certificates_to_check:
        # Verify essential Censys certificate fields
        assert "fingerprint_sha256" in certificate, "Each certificate should have a 'fingerprint_sha256' field"
        
        # Verify fingerprint format (basic validation)
        fingerprint = certificate["fingerprint_sha256"]
        assert isinstance(fingerprint, str), "Certificate fingerprint should be a string"
        assert len(fingerprint) == 64, "SHA256 fingerprint should be 64 characters long"
        
        # Check for names array which contains certificate subject alternative names and common names
        assert "names" in certificate, "Each certificate should have a 'names' field"
        names = certificate["names"]
        assert isinstance(names, list), "Certificate names should be a list"
        assert len(names) > 0, "Certificate names should not be empty"
        
        # Verify that at least one name matches our search query pattern
        google_names = [name for name in names if "google.com" in name.lower()]
        assert len(google_names) > 0, f"Certificate should contain google.com domain names, found: {names}"
        
        # Check for parsed certificate fields
        assert "parsed" in certificate, "Each certificate should have a 'parsed' field"
        parsed = certificate["parsed"]
        assert isinstance(parsed, dict), "Parsed certificate data should be a dictionary"
        
        # Check essential parsed certificate fields
        essential_parsed_fields = ["subject", "issuer", "validity", "signature_algorithm"]
        for field in essential_parsed_fields:
            if field in parsed:
                print(f"Certificate {fingerprint[:16]}... contains parsed field: {field}")
        
        # Check validity period
        if "validity" in parsed:
            validity = parsed["validity"]
            assert isinstance(validity, dict), "Validity should be a dictionary"
            
            validity_fields = ["start", "end", "length"]
            present_validity = [field for field in validity_fields if field in validity]
            print(f"Certificate validity contains: {', '.join(present_validity)}")
        
        # Check subject information
        if "subject" in parsed:
            subject = parsed["subject"]
            assert isinstance(subject, dict), "Subject should be a dictionary"
            
            subject_fields = ["common_name", "organization", "country", "locality"]
            present_subject = [field for field in subject_fields if field in subject]
            print(f"Certificate subject contains: {', '.join(present_subject)}")
        
        # Check issuer information
        if "issuer" in parsed:
            issuer = parsed["issuer"]
            assert isinstance(issuer, dict), "Issuer should be a dictionary"
            
            issuer_fields = ["common_name", "organization", "country"]
            present_issuer = [field for field in issuer_fields if field in issuer]
            print(f"Certificate issuer contains: {', '.join(present_issuer)}")
        
        # Check for additional optional certificate fields
        optional_fields = ["validation_level", "transparency", "tags", "zlint"]
        present_optional = [field for field in optional_fields if field in certificate]
        
        print(f"Certificate {fingerprint[:16]}... contains these optional fields: {', '.join(present_optional)}")
        
        # Check for certificate transparency logs
        if "transparency" in certificate:
            transparency = certificate["transparency"]
            assert isinstance(transparency, dict), "Transparency should be a dictionary"
            
            ct_fields = ["scts", "observed"]
            present_ct = [field for field in ct_fields if field in transparency]
            print(f"Certificate transparency contains: {', '.join(present_ct)}")
        
        # Log the structure of the first certificate for debugging
        if certificate == certificates_to_check[0]:
            print(f"Example certificate structure keys: {list(certificate.keys())}")
            if "parsed" in certificate:
                print(f"Example parsed certificate keys: {list(certificate['parsed'].keys())}")

    print(f"Successfully retrieved and validated {len(censys_certificates)} Censys certificates")

    return True