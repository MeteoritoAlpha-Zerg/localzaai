import pytest
from pydantic import ValidationError

from connectors.splunk.connector.tools import SplunkConnectorTools


class TestExecuteSplunkQueryModel:
    def test_valid_model(self):
        """Test that default vals are set correctly"""
        model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main")
        assert model.query == "search index=main"
        assert model.earliest == "-24h"
        assert model.latest == "now"
        assert model.limit == 100

    def test_all_fields(self):
        model = SplunkConnectorTools.ExecuteSplunkQueryInput(
            query="search index=main | head 10",
            earliest="-1h",
            latest="-5m",
            limit=50,
        )
        assert model.query == "search index=main | head 10"
        assert model.earliest == "-1h"
        assert model.latest == "-5m"
        assert model.limit == 50

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            SplunkConnectorTools.ExecuteSplunkQueryInput()

    def test_limit_validator(self):
        # as string
        model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", limit="25")
        assert model.limit == 25

        # as float
        model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", limit=25.5)
        assert model.limit == 25

        # invalid
        model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", limit="invalid")
        assert model.limit == 100

        # None
        model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", limit=None)
        assert model.limit == 100

    def test_model_dict(self):
        model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main")
        model_dict = model.model_dump()

        assert model_dict == {"query": "search index=main", "earliest": "-24h", "latest": "now", "limit": 100}

    def test_none_values(self):
        # Test with None values for optional fields
        model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", earliest=None, latest=None, limit=None)
        assert model.query == "search index=main"
        assert model.earliest == "-24h"
        assert model.latest == "now"
        assert model.limit == 100

    def test_relative_time_formats(self):
        """Test relative time formats are accepted without modification, and long values raise errors."""
        valid_relative_times = ["-24h", "+1d", "-7d", "@d", "-1m", "+4h", "1", "-180d"]
        invalid_relative_times = ["-1000d"]

        for time in valid_relative_times:
            model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", earliest=time, latest="now")
            assert model.earliest == time

            # Test on latest field too
            model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", latest=time)
            assert model.latest == time

        for time in invalid_relative_times:
            with pytest.raises(ValidationError) as exc_info:
                SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", earliest=time)
            assert "Invalid relative time format" in str(exc_info.value)

    def test_now_special_case(self):
        """Test that 'now' is accepted as is."""
        model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", earliest="now", latest="now")
        assert model.earliest == "now"
        assert model.latest == "now"

    def test_correct_absolute_format(self):
        """Test that already correct format passes validation."""
        correct_formats = ["2022-11-15T20:00:00", "2023-01-01T00:00:00", "2025-12-31T23:59:59"]

        for time in correct_formats:
            model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", earliest=time, latest=time)
            assert model.earliest == time
            assert model.latest == time

    def test_format_transformation(self):
        """Test transformation of various date formats to Splunk format."""
        test_cases = [
            # (input_format, expected_output)
            ("2025-03-26", "2025-03-26T00:00:00"),
            ("03-26-2025", "2025-03-26T00:00:00"),
            ("26/03/2025", "2025-03-26T00:00:00"),  # European format
            ("2023-12-25 14:30", "2023-12-25T14:30:00"),
            ("Dec 31, 2022 5pm", "2022-12-31T17:00:00"),
            ("January 15 2024", "2024-01-15T00:00:00"),
            ("2023.05.17", "2023-05-17T00:00:00"),
            ("20220228T145030", "2022-02-28T14:50:30"),  # ISO format without separators
            ("Feb 14, 2023 at 09:15", "2023-02-14T09:15:00"),
        ]

        for input_date, expected_output in test_cases:
            model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", earliest=input_date)
            assert model.earliest == expected_output

            model = SplunkConnectorTools.ExecuteSplunkQueryInput(query="search index=main", latest=input_date)
            assert model.latest == expected_output
