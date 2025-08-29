import pytest
from mongomock_motor import AsyncMongoMockClient  # type: ignore[import-untyped]

from common.managers.prioritization_rules.prioritization_rules_manager import (
    PrioritizationRuleException,
    PrioritizationRuleManager,
)
from common.managers.prioritization_rules.prioritization_rules_model import (
    PrioritizationRule,
)


@pytest.fixture(autouse=True)
async def prioritization_rule_manager():
    manager = PrioritizationRuleManager()
    collection = AsyncMongoMockClient()["metamorph_test"]["prioritization_rules"]
    await manager.initialize(collection)
    return manager


async def test_rules_not_exist(
    prioritization_rule_manager: PrioritizationRuleManager,
) -> None:
    rules = await prioritization_rule_manager.get_prioritization_rules_async()
    assert len(rules) == 0


async def test_get_all_rules(
    prioritization_rule_manager: PrioritizationRuleManager,
) -> None:
    metadata = PrioritizationRule(rule_name="name", field_name="field", field_regex="regex", priority_boost=1)
    await prioritization_rule_manager.upsert_prioritization_rule_async(metadata)

    m = await prioritization_rule_manager.get_prioritization_rules_async()
    assert len(m) == 1


async def test_upsert(prioritization_rule_manager: PrioritizationRuleManager) -> None:
    rule_name = "rule_name1"
    rule = PrioritizationRule(rule_name=rule_name, field_name="field", field_regex="regex", priority_boost=1)
    await prioritization_rule_manager.upsert_prioritization_rule_async(rule)
    saved_rule = await prioritization_rule_manager.get_prioritization_rule_async(rule_name)

    assert saved_rule is not None
    assert saved_rule.rule_name == rule_name

    saved_rule.field_name = "testfield"
    new_rule = await prioritization_rule_manager.upsert_prioritization_rule_async(saved_rule)
    assert new_rule.rule_name == "rule_name1"
    assert new_rule.field_name == "testfield"


async def test_insert(prioritization_rule_manager: PrioritizationRuleManager) -> None:
    rule_name = "rule_name1"
    metadata = PrioritizationRule(rule_name=rule_name, field_name="field", field_regex="regex", priority_boost=1)
    await prioritization_rule_manager.insert_prioritization_rule_async(metadata)
    with pytest.raises(
        PrioritizationRuleException,
        match=f"Unable to insert rule with name '{rule_name}' as it already exists",
    ):
        await prioritization_rule_manager.insert_prioritization_rule_async(metadata)


async def test_delete(prioritization_rule_manager: PrioritizationRuleManager) -> None:
    rule_name = "rule_name2"
    metadata = PrioritizationRule(rule_name=rule_name, field_name="field", field_regex="regex", priority_boost=1)
    await prioritization_rule_manager.upsert_prioritization_rule_async(metadata)

    await prioritization_rule_manager.delete_prioritization_rules_async(rule_names=[rule_name])

    all_rules = await prioritization_rule_manager.get_prioritization_rules_async()
    assert len(all_rules) == 0
