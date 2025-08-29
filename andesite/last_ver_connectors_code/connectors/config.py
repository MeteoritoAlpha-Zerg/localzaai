
from typing import Any, List, Optional, Self

from common.models.cron_config import CronConfig
from connectors.connector_id_enum import ConnectorIdEnum
from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.utils.fallback_none import fallback_none


class ConfigurableConnectorField(BaseModel):
    field_name: str
    configurable: Optional[bool] = False  # TODO: PROD-532
    value: int | str | bool

class ConnectorConfig(BaseSettings):
    """
    The ConnectorConfig defines the interface that connectors implement to define connector configuration they require.
    displayed_field_names will only be returned if given field names exist and have a value that's not None.
    """

    @classmethod
    def create(cls, id: ConnectorIdEnum) -> Self | None:
        prefix = f"{cls.__name__.removesuffix('ConnectorConfig').lower()}_"
        cls.model_config["env_prefix"] = prefix
        return fallback_none(lambda: cls(id=id))

    dev_verbose: bool = False
    displayable_field_names: List[str] = []

    model_config = SettingsConfigDict(
        extra="allow",
        env_ignore_empty=True,
        env_nested_delimiter="__",
    )

    # TODO: Will be used as the key when configs are derived from mongo
    id: ConnectorIdEnum

    enabled: bool = False
    available: bool = True

    configurable_field_names: List[str] = []

    token: SecretStr | None = None
    allows_user_token_management: bool = False

    indexing_token: SecretStr | None = None


class AlertSummaryTableConfig(BaseModel):
    friendly_name: str
    field_name: str
    link_format: Optional[str] = None
    link_replacements: Optional[List[tuple[str,str]]] = []

class AlertProviderConnectorConfig(ConnectorConfig):
    """
    A set of configurations for any connector that provides alerts.
    Overwrite in subclasses to provide appropriate defaults
    """

    mitre_attack_id_field_name: str = Field(
        description="Mitre attacks help determine alert priorities. This should indicate which field in the alert contains mitre ids.",
    )
    alert_title_format: str = Field(
        description="This determines the title of the alert card. The format is a string with placeholders for the field values.",
    )
    alert_description_format: str = Field(
        description="This determines the description of the alert card. The format is a string with placeholders for the field values.",
    )
    alert_summary_text_format: str = Field(
        description="This determines the summary text in the alert details. The format is a string with placeholders for the field values.",
    )
    alert_summary_table_configs: List[AlertSummaryTableConfig] = Field(
        description="This determines which fields are displayed in a summary table.",
    )

    @field_validator("alert_summary_table_configs", mode="after")
    @classmethod
    def _convert_from_dict_to_AlertSummaryTableConfig(cls, v: list[Any]) -> List[AlertSummaryTableConfig]:
        # when read in from the environment it is converted to a dictionary, so we must convert it back to an object
        v = [AlertSummaryTableConfig.model_validate(config) for config in v]
        return v
