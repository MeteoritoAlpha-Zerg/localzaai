from typing import Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch

from common.models.alerts import AlertDetailsLink, AlertDetailsTable, AlertFilter, AlertTime

from connectors.parse_alert_configs import parse_summary_table
from connectors.splunk.connector.alerts import get_splunk_alerts
from connectors.splunk.connector.config import AlertSummaryTableConfig
from connectors.splunk.database.splunk_instance import SplunkInstance


class MockedConfig:
    def __init__(self, mocked_lowest_priority: int):
        self.lowest_priority = mocked_lowest_priority


class MockSavedSearch:
    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content


mocked_lowest_priority = 1000


async def test_fetch_alerts():
    mock_splunk_instance = MagicMock(SplunkInstance)
    mock_splunk_instance.spl_query = AsyncMock()
    mock_splunk_instance._notable_index = "test_index"

    earliest = 3600
    latest = 0

    with patch.object(mock_splunk_instance, "fetch_alerts") as mock_fetch_alerts:
        await get_splunk_alerts(
            AlertFilter(earliest=earliest, latest=latest),
            "annotations.mitre_attack",
            mock_splunk_instance,
            [],
            "{search_name}",
            "{search_name}",
            "{search_name}",
        )

        mock_fetch_alerts.assert_called_once_with(f"-{earliest}s", f"-{latest}s")

    with patch.object(mock_splunk_instance, "fetch_alerts_by_ids") as mock_fetch_alerts_by_ids:
        await get_splunk_alerts(
            AlertFilter(alert_ids=["123"]),
            "annotations.mitre_attack",
            mock_splunk_instance,
            [],
            "{search_name}",
            "{search_name}",
            "{search_name}",
        )

        mock_fetch_alerts_by_ids.assert_called_once_with(alert_ids=["123"])


async def test_notables_index():
    mock = SplunkInstance(
        protocol="", host="", port=1, ssl_verification=False, token=None, es=False, notable_index="testme"
    )
    assert "testme" in mock._get_notable_index()

    mock = SplunkInstance(
        protocol="", host="", port=1, ssl_verification=False, token=None, es=True, notable_index="testme"
    )
    assert "testme" not in mock._get_notable_index()


async def test_link_replacement():
    data = AlertDetailsTable.model_validate(
        {
            "analytic_story": "Test story",
            "killchain": ["killchain1", "killchain2"],
            "annotations_mitre_attack": ["T1234", "T5678", "T90"],
            "annotations_mitre_attack_mitre_description": "Lorem ipsum dolor",
            "annotations_mitre_attack_mitre_tactic_id": ["T1234", "T1.234"],
        }
    )

    summary_table = parse_summary_table(
        [
            AlertSummaryTableConfig(
                friendly_name="Mitre Tactics",
                field_name="annotations_mitre_attack_mitre_tactic_id",
                link_format="https://attack.mitre.org/tactics/{0}",
                link_replacements=[(".", "/")],
            ),
        ],
        data,
    )
    assert summary_table is not None
    assert summary_table.get("Mitre Tactics") == [
        AlertDetailsLink(display_text='T1234', link='https://attack.mitre.org/tactics/T1234'),
        AlertDetailsLink(display_text='T1.234', link='https://attack.mitre.org/tactics/T1/234'),
    ]

async def test_parse_summary_table_duplicates():
    data = AlertDetailsTable.model_validate(
        {
            "analytic_story": "Test story",
            "killchain": ["killchain1", "killchain2"],
            "annotations_mitre_attack": ["T1234", "T1234", "T90"],
            "annotations_mitre_attack_mitre_description": "Lorem ipsum dolor",
            "annotations_mitre_attack_mitre_tactic_id": ["T1234", "T1234"],
        }
    )

    summary_table = parse_summary_table(
        [
            AlertSummaryTableConfig(
                friendly_name="Mitre Tactics",
                field_name="annotations_mitre_attack_mitre_tactic_id",
                link_format="https://attack.mitre.org/tactics/{0}",
                link_replacements=[(".", "/")],
            ),
        ],
        data,
    )
    assert summary_table is not None
    assert summary_table.get("Mitre Tactics") == [
        AlertDetailsLink(display_text='T1234', link='https://attack.mitre.org/tactics/T1234'),
    ]
