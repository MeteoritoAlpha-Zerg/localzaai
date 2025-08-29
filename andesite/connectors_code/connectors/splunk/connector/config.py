from typing import List, Optional

from pydantic import Field

from common.models.secret import StorableSecret
from connectors.config import AlertProviderConfigBase, AlertSummaryTableConfig, ConnectorConfigurationBase


class SplunkConnectorConfig(AlertProviderConfigBase, ConnectorConfigurationBase):
    protocol: str = "https"
    ssl_verification: bool = True
    host: str = "localhost"
    port: int = 8089
    app: str = "search"
    es: bool = False
    notable_index: str = "notable"
    notable_write_index: str = "andesite_alerts"
    data_indexing_lookback_seconds: int = 86400  # 24 hours
    query_timeout_seconds: int = 300  # 5 minutes

    mitre_attack_id_field_name: str = Field(
        default="annotations_mitre_attack",
        description="Mitre attacks help determine alert priorities. This should indicate which field in the alert contains mitre ids.",
    )
    alert_title_format: str = Field(
        default="{rule_title}",
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
    token: Optional[StorableSecret] = None
    delete_token: Optional[StorableSecret] = None
    # The splunk token associated with the scheduled index caching task
    # TODO: https://andesite.atlassian.net/browse/PROD-789 we should pass user token to index the data. customers shouldn't be expected to provide this
    indexing_token: Optional[StorableSecret] = None

    # If we want to do mtls with the splunk client
    use_mtls: Optional[bool] = None
    mtls_client_cert_path: Optional[str] = None
    mtls_client_key_path: Optional[str] = None
    mtls_client_cert_data: Optional[StorableSecret] = None
    mtls_client_key_data: Optional[StorableSecret] = None

    # If we want to use oauth to grab a client access token these fields are required
    token_oauth_hostname: Optional[str] = None
    token_oauth_client_id: Optional[StorableSecret] = None
    token_oauth_client_secret: Optional[StorableSecret] = None

    # If the splunk instance is "re-homed" (the REST API root is not running at `/`)
    # We can use this variables to change the path prefix to splunk
    uri_add_prefix: Optional[str] = None  # The portion of the path to prepend to what is left after the strip
