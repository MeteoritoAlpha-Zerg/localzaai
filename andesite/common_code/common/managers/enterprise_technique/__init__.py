from pathlib import Path

from common.managers.enterprise_technique.enterprise_technique_manager import (
    EnterpriseTechniqueManager,
)

EnterpriseTechniqueManager.instance().load_initial_techniques(Path(__file__).parent / "default_mitre_values")
