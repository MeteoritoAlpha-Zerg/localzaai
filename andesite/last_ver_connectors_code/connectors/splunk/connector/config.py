from typing import List, Optional

from pydantic import Field, SecretStr

from connectors.config import AlertProviderConnectorConfig, AlertSummaryTableConfig

class SplunkConnectorConfig(AlertProviderConnectorConfig):
    protocol: str = "https"
    ssl_verification: bool = True
    host: str = "localhost"
    port: int = 8089
    app: str = "search"
    es: bool = False
    notable_index: str = "notable_demo"
    data_indexing_lookback_seconds: int = 86400  # 24 hours in seconds

    mitre_attack_id_field_name: str = Field(
        default="annotations_mitre_attack",
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
            AlertSummaryTableConfig(
                friendly_name="Analytic Story", field_name="analytic_story"
            ),
            AlertSummaryTableConfig(friendly_name="Source IP", field_name="src_ip"),
            AlertSummaryTableConfig(
                friendly_name="Destination IP", field_name="dest_ip"
            ),
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
    delete_token: Optional[SecretStr] = None
    # The splunk token associated with the scheduled index caching task
    # TODO: https://andesite.atlassian.net/browse/PROD-789 we should pass user token to index the data. customers shouldn't be expected to provide this
    indexing_token: Optional[SecretStr] = None

    # If we want to do mtls with the splunk client
    use_mtls: Optional[bool] = None
    mtls_client_cert_path: Optional[str] = None
    mtls_client_key_path: Optional[str] = None
    mtls_client_cert_data: Optional[SecretStr] = None
    mtls_client_key_data: Optional[SecretStr] = None

    # If we want to use oauth to grab a client access token these fields are required
    token_oauth_hostname: Optional[str] = None
    token_oauth_client_id: Optional[SecretStr] = None
    token_oauth_client_secret: Optional[SecretStr] = None

    # If the splunk instance is "re-homed" (the REST API root is not running at `/`)
    # We can use this variables to change the path prefix to splunk
    uri_add_prefix: Optional[str] = (
        None  # The portion of the path to prepend to what is left after the strip
    )

    displayable_field_names: List[str] = [
        "protocol",
        "host",
        "port",
        "mitre_attack_id_field_name",
        "alert_title_format",
        "alert_description_format",
        "alert_summary_text_format",
        "alert_summary_table_configs",
    ]
