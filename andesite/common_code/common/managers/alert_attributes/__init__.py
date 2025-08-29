from pathlib import Path

from common.managers.alert_attributes.alert_attribute_manager import (
    AlertAttributeManager,
)

AlertAttributeManager.instance().load_initial_data(Path(__file__).parent / "default_alert_attributes")
