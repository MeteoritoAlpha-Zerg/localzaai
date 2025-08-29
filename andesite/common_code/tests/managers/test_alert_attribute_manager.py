from datetime import UTC, datetime

from bson import ObjectId

from common.managers.alert_attributes.alert_attribute_model import AlertAttributeDb
from common.models.alert_attributes import AlertAttribute, AlertAttributeContext
from common.models.connector_id_enum import ConnectorIdEnum


def test_attribute_get_weight_none():
    model = AlertAttribute(
        id="1",
        attribute_name="test_attribute",
        mappings={},
        context_weights={},
        created_at=datetime.now(UTC),
    )
    assert model.weight(AlertAttributeContext.grouping) == 0.0


def test_attribute_get_weight():
    model = AlertAttribute(
        id="1",
        attribute_name="test_attribute",
        mappings={},
        context_weights={AlertAttributeContext.grouping: 7.0},
        created_at=datetime.now(UTC),
    )
    assert model.weight(AlertAttributeContext.grouping) == 7.0


def test_attribute_from_db():
    id = ObjectId()
    document = AlertAttributeDb(
        id=id,
        attribute_name="test_attribute",
        mappings={"splunk": ["test"]},
        context_weights={"grouping": 7.0},
    )
    model = AlertAttribute.from_db(document)
    creation_time = id.generation_time.astimezone(tz=UTC)
    assert model == AlertAttribute(
        id=str(id),
        attribute_name="test_attribute",
        mappings={ConnectorIdEnum.SPLUNK: ["test"]},
        context_weights={AlertAttributeContext.grouping: 7.0},
        created_at=creation_time,
    )


def test_attribute_to_db():
    id = ObjectId()
    creation_time = id.generation_time.astimezone(tz=UTC)
    model = AlertAttribute(
        id=str(id),
        attribute_name="test_attribute",
        mappings={ConnectorIdEnum.SPLUNK: ["test"]},
        context_weights={AlertAttributeContext.grouping: 7.0},
        created_at=creation_time,
    )
    assert model.to_db() == AlertAttributeDb(
        id=id,
        attribute_name="test_attribute",
        mappings={"splunk": ["test"]},
        context_weights={"grouping": 7.0},
    )
