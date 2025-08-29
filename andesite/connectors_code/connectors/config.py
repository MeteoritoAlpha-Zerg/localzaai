from enum import StrEnum, auto
from opentelemetry import trace
from typing import Any, List, Optional, Self

from pydantic_settings import SettingsConfigDict

from common.jsonlogging.jsonlogger import Logging
from common.models.connector_id_enum import ConnectorIdEnum
from pydantic import AliasChoices, BaseModel, Field, field_validator

from functools import lru_cache

from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection

from typing import Any, Callable, Optional, Self

from common.models.connector_id_enum import ConnectorIdEnum

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)

class ConfigurableConnectorFieldTypeEnum(StrEnum):
    BOOLEAN = auto()
    STRING = auto()
    NUMBER = auto()
    SECRET = auto()
    COMPLEX = auto()
    """
    Complex represents any json encodable object
    """

class ConfigurableConnectorField(BaseModel):
    field_name: str
    field_type: ConfigurableConnectorFieldTypeEnum
    value: Any

DEFAULT_HIDDEN_FIELDS = ["id"]

class ConnectorConfigurationBase(BaseModel):
    """
    The ConnectorConfigurationBase defines the interface that connectors implement to define connector configuration they require.
    """
    model_config = SettingsConfigDict(
        extra="allow",
    )

    id: ConnectorIdEnum = Field(
        serialization_alias="_id",
        validation_alias=AliasChoices("id", "_id"),
    )

    enabled: bool = False
    """
    Denotes whether a connector is live for a site.

    To be enabled; a connector must be both available and correctly configured
    """

    hidden_fields: list[str] = DEFAULT_HIDDEN_FIELDS
    """
    Allows some fields to be hidden from the end user

    Should at least always contain the "id" field
    """

class AlertSummaryTableConfig(BaseModel):
    friendly_name: str
    field_name: str
    link_format: Optional[str] = None
    link_replacements: Optional[List[tuple[str, str]]] = []


class AlertProviderConfigBase(BaseModel):  # pragma: no cover
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

class ConnectorConfigurationException(Exception):
    """Base class for exceptions in this module."""

    pass


class ConnectorConfigurationManager:
    def __init__(
        self,
    ):
        """
        Initializes the ConnectorConfigurationManager.

        :return: None
        """
        self._storage_collection: AgnosticCollection | None = None
        self._internal_default_configurations: dict[ConnectorIdEnum, Any] = {}

    @staticmethod
    def check_client_initialization(function: Any) -> Callable[..., Any]:
        def check_client(self: Self, *args: Any, **kwargs: Any):
            if self._storage_collection is None:
                raise ConnectorConfigurationException("No storage collection initialized")
            return function(self, *args, **kwargs)

        return check_client

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "ConnectorConfigurationManager":
        """
        Get a global singleton of the ConnectorConfigurationManager in a threadsafe manner.
        :return: The app-wide ConnectorConfigurationManager singleton.
        """
        return ConnectorConfigurationManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("initialize")
    async def initialize(
        self, storage_collection: Optional[AgnosticCollection] = None
    ) -> None:
        """
        Initializes the ConnectorConfigurationManager with a storage collection.

        :param storage_collection: The storage collection to use.
        :return: None
        """
        if self._storage_collection is not None:
            logger().warning(
                "ConnectorConfigurationManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "ConnectorConfigurationManager initialized without a storage collection - dataset descriptions will not be persisted"
            )
            return

    @check_client_initialization
    async def ensure_configuration_entry_present(self, connector: ConnectorIdEnum) -> None:
        """
        Given a connector we make sure we have a configuration entry available for it.

        Even if not configured, this will make the connector available to this customer.
        """
        try:
            await self._storage_collection.insert_one({ "_id": connector, "enabled": False }) # type: ignore
        except DuplicateKeyError:
            pass

    @check_client_initialization
    async def get_configuration(self, connector: ConnectorIdEnum) -> ConnectorConfigurationBase:
        """
        Given a connector we make sure we have a configuration entry available for it.

        Even if not configured, this will make the connector available to this customer.
        """
        result = await self._storage_collection.find_one({ "_id": connector }) # type: ignore
        if result is None:
            raise ConnectorConfigurationException(f"Unable to find configuration for connector: {connector}")

        return ConnectorConfigurationBase.model_validate(result)

    @check_client_initialization
    async def put_configuration(self, connector: ConnectorIdEnum, config: ConnectorConfigurationBase) -> ConnectorConfigurationBase:
        """
        Given a connector we make sure we have a configuration entry available for it.

        Even if not configured, this will make the connector available to this customer.
        """
        result = await self._storage_collection.find_one_and_update({ "_id": connector }, { "$set": config.model_dump() }, return_document=True) # type: ignore
        if result is None:
            raise ConnectorConfigurationException(f"Unable to update configuration for connector: {connector}")

        return ConnectorConfigurationBase.model_validate(result)
