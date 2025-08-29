import datetime

from common.managers.prioritization_rules.prioritization_rules_model import (
    PrioritizationRule,
)
from common.models.alerts import (
    Alert,
    AlertDetailsTable,
)

from connectors.connector_id_enum import ConnectorIdEnum


async def test_assigning_priority():
    data: dict[str, str | list[str]] = {
        "analytic_story": "Test story",
        "killchain": ["killchain1", "killchain2"],
        "annotations_mitre_attack": ["T1234", "T5678", "T90"],
        "annotations_mitre_attack_mitre_description": "Lorem ipsum dolor",
        "annotations_mitre_attack_mitre_tactic_id": "T1234",
    }
    alert = Alert(
        id="123",
        categories=[],
        description="description",
        connector=ConnectorIdEnum.SPLUNK,
        time=datetime.datetime.now(),
        title="test",
        details_table=AlertDetailsTable.model_validate(data),
    )

    alert.assign_alert_priority(
        highest_mitre_priority=10,
        priority_boosts=[],
    )
    assert alert.priority == 10

    alert.priority = 999
    alert.assign_alert_priority(
        priority_boosts=[
            PrioritizationRule(
                rule_name="test",
                field_name="annotations_mitre_attack_mitre_tactic_id",
                field_regex="T1234",
                priority_boost=0.5,
            )
        ],
        highest_mitre_priority=10,
    )
    assert alert.priority == 5
