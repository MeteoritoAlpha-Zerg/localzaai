from typing import List

from pydantic import Field

from common.models.secret import StorableSecret
from connectors.config import AlertProviderConfigBase, AlertSummaryTableConfig, ConnectorConfigurationBase


class ElasticConnectorConfig(AlertProviderConfigBase, ConnectorConfigurationBase):
    url: str
    api_key: StorableSecret
    alert_index: str = ""

    mitre_attack_id_field_name: str = Field(
        default="kibana.alert.rule.threat",
        description="Mitre attacks help determine alert priorities. This should indicate which field in the alert contains mitre ids.",
    )
    alert_title_format: str = Field(
        default="{killchain}",
        description="This determines the title of the alert card. The format is a string with placeholders for the field values.",
    )
    alert_description_format: str = Field(
        default="{analytic_story} ({annotations_mitre_attack} / {annotations_mitre_attack_mitre_technique}) was detected on host {dest_ip}",
        description="This determines the description of the alert card. The format is a string with placeholders for the field values.",
    )
    alert_summary_text_format: str = Field(
        default="{mitre_technique_description}",
        description="This determines the summary text in the alert details. The format is a string with placeholders for the field values.",
    )
    alert_summary_table_configs: List[AlertSummaryTableConfig] = Field(
        description="This determines which fields are displayed in a summary table.",
        default=[
            AlertSummaryTableConfig(friendly_name="Analytic Story", field_name="analytic_story"),
            AlertSummaryTableConfig(friendly_name="Source IP", field_name="src_ip"),
            AlertSummaryTableConfig(friendly_name="Destination IP", field_name="dest_ip"),
            AlertSummaryTableConfig(
                friendly_name="Mitre Technique",
                field_name="annotations_mitre_attack",
                link_format="https://attack.mitre.org/techniques/{}",
                link_replacements=[(".", "/")],
            ),
            AlertSummaryTableConfig(
                friendly_name="Mitre Tactics",
                field_name="annotations_mitre_attack_tactic_id",
                link_format="https://attack.mitre.org/tactics/{0}",
                link_replacements=[(".", "/")],
            ),
        ],
    )
