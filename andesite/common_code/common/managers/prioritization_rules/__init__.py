from pathlib import Path

from common.managers.prioritization_rules.prioritization_rules_manager import (
    PrioritizationRuleManager,
)

PrioritizationRuleManager.instance().load_initial_rules(Path(__file__).parent / "default_prioritization_rules")
