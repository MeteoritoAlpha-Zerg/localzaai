from unittest.mock import patch, MagicMock
from connectors.equinox.database.equinox_instance import (
    CensysHost,
    CensysHostSearchPredictionModel,
    EquinoxInstance,
    preview_censys_records,
)
from tests.equinox.censys_records import fake_censys_records


def test_censys_host():
    for record in preview_censys_records(fake_censys_records):
        host_record = CensysHost(**record)
        assert isinstance(host_record, CensysHost)


@patch("connectors.equinox.database.equinox_instance.requests.post")
def test_fetch_one_host(mock_post):
    equinox_instance = EquinoxInstance(protocol="http", host="127.0.0.1", port=8000)
    query = CensysHostSearchPredictionModel(
        search_ip="203.0.113.45", search_snapshot_date="2024-10-14"
    )

    # Setup the mock post response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "host_identifier": {"ipv4": "203.0.113.45"},
        "date": "2024-10-14",
        "location": {"country": "United States"},
        "services": [],
        "operating_system": {"uniform_resource_identifier": "Ubuntu 20.04"},
        "dns": {"names": ["example.com"]},
    }
    mock_post.return_value = mock_response

    result = equinox_instance.fetch_one_host(query)

    assert isinstance(result, dict), "result is not a dict"
    assert set(result.keys()) == set(
        [
            "ip",
            "snapshot_date",
            "l2",
            "services",
            "location",
            "operating_system",
            "dns",
        ]
    ), "fields do not match"


@patch("connectors.equinox.database.equinox_instance.requests.post")
def test_query_censys_host_search(mock_post):
    equinox_instance = EquinoxInstance(protocol="http", host="127.0.0.1", port=8000)
    query = CensysHostSearchPredictionModel(
        search_ip="203.0.113.45", search_snapshot_date="2024-10-14"
    )

    # Setup the mock post response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"records": fake_censys_records}
    mock_post.return_value = mock_response

    results = equinox_instance.query_censys_host_search(query)

    assert isinstance(results, list), "result is not a list"

    keys = set()
    for record in results:
        keys.update(set(record.keys()))

    assert keys == set(
        [
            "ip",
            "snapshot_date",
            "l2",
            "services",
            "location",
            "operating_system",
            "dns",
        ]
    ), "fields do not match"
