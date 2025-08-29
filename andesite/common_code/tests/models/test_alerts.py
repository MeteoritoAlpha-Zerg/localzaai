from datetime import datetime

import pytest

from common.models.alerts import Alert, AlertDetailsLink, AlertDetailsTable
from common.models.connector_id_enum import ConnectorIdEnum


@pytest.fixture
def original_details_table():
    return AlertDetailsTable.model_validate(
        {
            "field1": "Test value 1",
            "field2": ["item1", "item2"],
            "field3": ["T1234", "T5678", "T90"],
            "field4": None,
            "field5": "tactic1\r\ntactic2\r\ntactic3",
            "field6.testing": "removed",
            "field6": {"testing": "test"},
        }
    )


@pytest.fixture
def alert(original_details_table):
    return Alert(
        id="123",
        time=datetime.now(),
        connector=ConnectorIdEnum.SPLUNK,
        title="splunk alert",
        description="description",
        details_table=original_details_table,
        summary_table={"test": [AlertDetailsLink(display_text="test", link="test")]},
    )


def test_copy_translated_details_table(alert, original_details_table):
    alert_copy = alert.copy_with_translated_details_table(
        {
            "field1": "canonical_field1",
            "field3": "canonical_field3",
            "field7": "canonical_field2",
        }
    )
    assert alert is not alert_copy
    assert alert_copy.get_details_table_as_dict() == {
        "canonical_field1": "Test value 1",
        "field2.0": "item1",
        "field2.1": "item2",
        "canonical_field3.0": "T1234",
        "canonical_field3.1": "T5678",
        "canonical_field3.2": "T90",
        "field4": None,
        "field5": "tactic1\r\ntactic2\r\ntactic3",
        "field6.testing": "test",
    }


def test_copy_translated_details_table_exclude_is_true(alert, original_details_table):
    alert_copy = alert.copy_with_translated_details_table(
        {"field1": "canonical_field1", "field3": "canonical_field3"}, exclude=True
    )
    assert alert is not alert_copy
    details_dict = alert_copy.get_details_table_as_dict()
    assert details_dict == {
        "canonical_field1": "Test value 1",
        "canonical_field3.0": "T1234",
        "canonical_field3.1": "T5678",
        "canonical_field3.2": "T90",
    }


def test_copy_translated_details_table_does_not_overwrite_existing_field(alert, original_details_table):
    original_details_table_as_dict = original_details_table.model_dump()
    alert_copy = alert.copy_with_translated_details_table({"field3": "field1", "field2": "canonical_field2"})
    alert_copy_as_dict = alert_copy.get_details_table_as_dict()
    assert alert is not alert_copy
    assert alert_copy_as_dict["field1"] == original_details_table_as_dict["field1"]
    assert "field2" not in alert_copy_as_dict


def test_copy_translated_details_table_no_fields(alert, original_details_table):
    alert_copy = alert.copy_with_translated_details_table({})
    assert alert is not alert_copy
    assert alert_copy.details_table == original_details_table


def test_get_detail_value(alert, original_details_table):
    field_name = "field2"
    assert alert.get_detail_value(field_name) == ["item1", "item2"]
    assert alert.get_detail_value(field_name + ".1") == "item2"

    assert alert.get_detail_value("field6") == {"testing": "test"}
    assert alert.get_detail_value("field6.testing") == "test"

    assert alert.get_detail_value("not_a_field") is None


def test_get_field_keys(alert, original_details_table):
    assert alert.details_table.get_field_keys("field3") == [
        "field3.0",
        "field3.1",
        "field3.2",
    ]
    assert alert.details_table.get_field_keys("field6") == ["field6.testing"]


def test_set_detail_value_writes_value(alert, original_details_table):
    new_value = 2
    field_name = "new_field_2"
    alert._set_detail_value(field_name, new_value)
    assert alert.get_details_table_as_dict()[field_name] == new_value


def test_set_detail_value_does_not_overwrite_field(alert, original_details_table):
    new_value = 2
    field_name = "field2"
    alert._set_detail_value(field_name, new_value)
    assert alert.get_details_table_as_dict() == original_details_table.model_dump()


def test_delete_detail(alert):
    alert._delete_detail_value("field5")
    assert alert.details_table.model_dump() == {
        "field1": "Test value 1",
        "field2.0": "item1",
        "field2.1": "item2",
        "field3.0": "T1234",
        "field3.1": "T5678",
        "field3.2": "T90",
        "field4": None,
        "field6.testing": "test",
    }


def test_delete_detail_not_exists(alert, original_details_table):
    alert._delete_detail_value("not_a_field")
    assert alert.details_table == original_details_table


def test_fields(alert):
    field_names = alert.fields()
    assert field_names == {
        "field1",
        "field2.0",
        "field2.1",
        "field3.0",
        "field3.1",
        "field3.2",
        "field4",
        "field5",
        "field6.testing",
    }


@pytest.mark.parametrize(
    "other_details_table,expected_matching_fields",
    [
        (
            {"field3": ["T1234", "T5678", "T90"], "field1": "Test value 1"},
            {"field3.0", "field3.1", "field3.2", "field1"},
        ),
        (
            {"field3": ["T1234", "T5678"], "field1": "Test value 1"},
            {"field3.0", "field3.1", "field1"},
        ),
        ({"field3": None}, set()),
        ({"field1": "test"}, set()),
        ({"field6": "test"}, set()),
        ({}, set()),
    ],
)
def test_matching_fields(alert, other_details_table, expected_matching_fields):
    other_alert = Alert(
        id="345",
        time=datetime.now(),
        connector=ConnectorIdEnum.ELASTIC,
        title="elastic alert",
        description="description 2",
        details_table=other_details_table,
        summary_table={"test": [AlertDetailsLink(display_text="test", link="test")]},
    )
    assert alert.matching_fields(other_alert) == expected_matching_fields


def test_empty_alert_details_table_matching_fields():
    alert1 = Alert(
        id="345",
        time=datetime.now(),
        connector=ConnectorIdEnum.ELASTIC,
        title="elastic alert",
        description="description 2",
    )
    alert2 = Alert(
        id="345",
        time=datetime.now(),
        connector=ConnectorIdEnum.ELASTIC,
        title="elastic alert",
        description="description 2",
    )
    assert alert1.matching_fields(alert2) == set()


def test_matches_id(alert):
    other_alert = Alert(
        id="123",
        time=datetime.now(),
        connector=ConnectorIdEnum.ELASTIC,
        title="elastic alert",
        description="description 2",
    )
    assert alert.matches_id(other_alert)


def test_does_not_match_id(alert):
    other_alert = Alert(
        id="345",
        time=datetime.now(),
        connector=ConnectorIdEnum.ELASTIC,
        title="elastic alert",
        description="description 2",
    )
    assert not alert.matches_id(other_alert)
