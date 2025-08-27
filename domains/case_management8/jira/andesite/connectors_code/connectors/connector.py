import asyncio
from abc import abstractmethod
from pathlib import Path
from typing import Any, Awaitable, Callable, Generic, List, Optional, Self, Type, TypeVar, Union, get_args, get_origin

from cachetools import TTLCache
from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
    UpsertDatasetDescription,
)
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure
from common.managers.enterprise_technique.enterprise_technique_manager import (
    EnterpriseTechniqueManager,
)
from common.managers.prioritization_rules.prioritization_rules_manager import (
    PrioritizationRuleException,
    PrioritizationRuleManager,
)
from common.managers.user.user_manager import UsersManager
from common.models.alerts import (
    Alert,
    AlertFilter,
    ConnectorGenerateAlert,
)
from common.models.connector_id_enum import ConnectorIdEnum
from common.models.secret import StorableSecret
from common.models.tool import Tool
from opentelemetry import trace
from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError

from connectors.config import DEFAULT_HIDDEN_FIELDS, ConfigurableConnectorField, ConfigurableConnectorFieldTypeEnum, ConnectorConfigurationBase
from connectors.cache import Cache
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
)

alerts_cache: TTLCache[str, list[Alert]] = TTLCache(maxsize=10, ttl=30)

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)
ddm = DatasetDescriptionManager.instance()

def _could_be_type(field_type: type[Any], target_type: type[Any]) -> bool:
    """
    Programmatically sees if the field type could accept a value of target type
    """
    origin = get_origin(field_type)

    if origin is Union:
        return any(_could_be_type(arg, target_type) for arg in get_args(field_type))
    if origin is list:
        return get_origin(target_type) is list and get_args(field_type) == get_args(target_type)

    return issubclass(field_type, target_type)

class UninitializedConnectorError(ValueError):
    """
    An error representing if a connector is not initialized

    If this is thrown you are probably not getting connector instances correctly!
    Please only retrieve connector instances through the ConnectorRegistry!
    """

    pass


class UnsupportedOperationError(ValueError):
    """
    An error representing if a connector does not support the requested functionality
    """

    pass


class ConnectorTargetInterface(BaseModel):
    """
    The ConnectorTargetInterface defines the interface that connectors implement to define query target information such
    as data source or collections.

    The query target defines what datasets the agent is allowed to query.
    """

    model_config = ConfigDict(extra="allow")

    @abstractmethod
    def get_dataset_paths(self) -> list[list[str]]:
        """
        A single connector target can point to many sets of data (e.g. multiple splunk indexes)

        Returns a list of paths that point to these datasets.

        One example use case: this will return every unique dataset that could have an associated description for a given target
        """
        pass

class ConnectorSecretsInterface(BaseModel):
    """
    This interface defines what secrets are available for this connector.

    This should be extended and created by using the token retrieval function provided to this connector
    """

    model_config = ConfigDict(extra="allow")


class ConnectorInfo(BaseModel):
    """
    This is any information that is relevant to knowing what this connector does and where it may be useful.
    """

    id: ConnectorIdEnum
    display_name: str
    enabled: bool
    configured: bool
    beta: bool
    """
    A beta connector is any connector that we theoretically support, but have no internal instance of the provider running, so cannot validate our approach/quality.

    Please be cautious of adding beta connectors
    """
    description: str
    can_enrich_alerts: bool
    can_generate_alerts: bool
    has_alerts: bool
    has_configurable_query_target: bool
    has_indexed_data: bool
    has_user_token_management: bool
    has_dataset_descriptions: bool


TConfig = TypeVar("TConfig", bound=ConnectorConfigurationBase)
TTarget = TypeVar("TTarget", bound=ConnectorTargetInterface)
TSecrets = TypeVar("TSecrets", bound=ConnectorSecretsInterface)


class Connector(Generic[TConfig, TTarget, TSecrets]):
    """
    A connector is Metamorph's interface to interacting with a customer's external systems.

    These systems enable a variety of verticals across metamorph, such as:
        1. Enrichment - A connector can bring additional context to existing data
            e.g. "Tell me more about this website: example.com"
        2. Alert Provider - Connectors can map their internal SIEM (or similar) alerts to our central alert feed
        3. Query - A query connector allows the agent to build queries to explore and analyze our customer's data
            e.g. "How many alerts have there been over the last week?"

    Any configured connector will be automatically registered and available to the user to chat with.
    Depending on what functionality is provided to the constructor, connectors will dynamically provided across the platform.
    The agent will be provided enabled connectors through the chat and will interact with them through their provided tools.
    """

    config: TConfig | None

    cache: Cache | None

    user_id: str | None
    """
    A user id must be provided to fetch this connector's configuration from the database. If no user id is provided, this connector will be limited in functionality
    """
    encryption_key: str | None
    """
    If this connector relies on any secrets in it's configuration, an encryption key matching what the secret was encrypted with MUST be provided if the secrets need to be used, or else the secrets will stay encrypted
    """

    def __init__(
        self,
        id: ConnectorIdEnum,
        display_name: str,
        description: str,
        logo_path: Path,
        config_cls: Type[TConfig],
        query_target_type: Type[TTarget],
        get_tools: Callable[[TConfig, TTarget, TSecrets, Cache | None], list[Tool]],
        get_secrets: Callable[[TConfig, str, SecretStr | None], Awaitable[TSecrets | None]],
        beta: bool = False,
        check_connection: Callable[[TConfig, TSecrets], Awaitable[bool]] | None = None,
        get_alert_enrichment_prompt: Callable[[], str] | None = None,
        get_alerts: Callable[[TConfig, TSecrets, AlertFilter, Cache | None], Awaitable[list[Alert]]] | None = None,
        generate_alert: Callable[[TConfig, TSecrets, ConnectorGenerateAlert], Awaitable[None]] | None = None,
        delete_generated_alerts: Callable[[TConfig, TSecrets], Awaitable[None]] | None = None,
        get_does_allow_user_token_management: Callable[[TConfig], bool] | None = None,
        get_query_target_options: Callable[[TConfig, TSecrets], Awaitable[ConnectorQueryTargetOptions]] | None = None,
        merge_data_dictionary: Callable[
            [TConfig, TSecrets, list[DatasetDescription], list[str]], Awaitable[list[DatasetDescription]]
        ]
        | None = None,
        get_dataset_structure_to_index: Callable[[TConfig, TSecrets, TTarget | None], Awaitable[list[DatasetStructure]]]
        | None = None,
    ) -> None:
        """
        :display_name: the name for this connector that will be **displayed to the end user**
        :description: a human friendly description for this connector. **This will be displayed to the end user**
        :query_target_type: a query target is how we specify what data the agent is allowed to query into. An agent can only query data explicitly allowed in the query target
        :get_tools: tools are explicitly for the agent and only the agent. Every other functionality provided by this interface is to serve the end user, but the tools are provided to the agent as its way of interacting with this connector (and thus external system)
        :get_secrets: given an encryption key and potentially a user token, decrypt and provide the SecretStr secrets for this connector
        :check_connection: this can be optionally provided to let the user verify they have correctly configured this connector
        :get_alert_enrichment_prompt: if this connector can enrich incoming data, this prompt can be provided for the agent to know when this connector should be used to do so
        :get_alerts: if provided, this will allow alerts from this connector to be rendered in metamorph's primary "Feed" page
        :generate_alert: this allows us to send alerts to a customer's external systems
        :delete_generated_alerts: if provided, administrators will use this to clear any alerts we have generated on customers' external systems
        :get_does_allow_user_token_management: can be evaluated to see if users can manage their own token for this connector. If not provided this feature will be disabled and only global secrets will be used
        :get_query_target_options: can be called to get the query target options the user can then select from when querying this connector. The agent will respect the configured query target and only ever access datasets the user has explicitly allowed
        :merge_data_dictionary: a function that handles the merging of stored data dictionary descriptions with those that exist on external systems
        :get_dataset_structure_to_index: if a connector has a complicated data structure you can provide this function for us to index the provided dataset structure. This will allow us to inspect the external data model without having to reach out to any external systems
        """
        self.id = id
        self.display_name = display_name
        self.description = description
        self.logo_path = logo_path
        self.query_target_type = query_target_type
        self._config_cls = config_cls
        self._beta = beta
        self._get_tools = get_tools
        self._get_connector_secrets = get_secrets
        self._check_connection = check_connection
        self._get_alert_enrichment_prompt = get_alert_enrichment_prompt
        self._get_alerts = get_alerts
        self._generate_alert = generate_alert
        self._delete_generated_alerts = delete_generated_alerts
        self._get_query_target_options = get_query_target_options
        self._merge_data_dictionary = merge_data_dictionary
        self._get_does_allow_user_token_management = get_does_allow_user_token_management
        self._get_dataset_structure_to_index = get_dataset_structure_to_index

    async def initialize(self, config: ConnectorConfigurationBase, cache: Cache | None, user_id: str | None, encryption_key: str) -> Self:
        try:
            self.config = self._config_cls.model_validate(config.model_dump(), context={"encryption_key": encryption_key})
        except ValidationError as ve:
            logger().warning(f"Unable to initialize connector {self.id} due to incorrect configuration. Validation Errors: {ve.errors()}")
            self.config = None

        self.cache = cache
        # We scope every connector to user and encryption key. then use these to derive any token internally/externally.
        self.user_id = user_id
        # Encryption key is going to be needed when storing connector configs in mongo
        self.encryption_key = encryption_key
        return self

    def get_info(self) -> ConnectorInfo:
        has_user_token_management = (
            self._get_does_allow_user_token_management(self.config)
            if self.config and self._get_does_allow_user_token_management
            else False
        )

        return ConnectorInfo(
            id=self.id,
            display_name=self.display_name,
            enabled=self.config is not None and self.config.enabled,
            beta=self._beta,
            configured=self.config is not None,
            description=self.description,
            can_generate_alerts=self._generate_alert is not None,
            can_enrich_alerts=self._get_alert_enrichment_prompt is not None,
            has_alerts=self._get_alerts is not None,
            has_configurable_query_target=self._get_query_target_options is not None,
            has_indexed_data=self._get_dataset_structure_to_index is not None,
            has_user_token_management=has_user_token_management,
            has_dataset_descriptions=self._merge_data_dictionary is not None,
        )

    async def _get_secrets(self) -> TSecrets | None:
        """
        Retrieves the secrets to be used for authentication

        The connector must be initialized and we will retrieve the user's connector token if allowed

        Connectors will then perform authentication/retrieval at their discretion.
        e.g. the splunk connector will authenticate through oauth
        """
        # Use the user's token if the connector allows it
        info = self.get_info()
        user_token = None
        if info.has_user_token_management and self.user_id is not None and self.encryption_key is not None:
            user = await UsersManager.get_user(id=self.user_id)
            if not user:
                raise ValueError("Unable to find requested user for token retrieval")
            user_token = user.tokens.decrypt_token(encryption_key=self.encryption_key, token_name=ConnectorIdEnum.SPLUNK)

        if self.config is not None and self.encryption_key is not None:
            return await self._get_connector_secrets(self.config, self.encryption_key, user_token)

        return None

    async def get_tools(self, target: TTarget) -> list[Tool]:
        """
        Retrieves a list of tool that will be utilized by the agent.

        The agent will only be able to interact with this connector through these returned tools.
        """
        if self.config is None or self.config.enabled is False:
            return []

        secrets = await self._get_secrets()
        if secrets is None:
            logger().warning("Connector is missing token configuration, unable to provide tools")
            return []

        return self._get_tools(self.config, target, secrets, self.cache)

    async def check_connection(self) -> bool:
        """
        Allows us to validate this connector is configured correctly and the external system can be reached
        """
        if not self.config:
            raise UninitializedConnectorError()


        secrets = await self._get_secrets()
        if secrets is None:
            logger().warning("Connector is missing token configuration, unable to check connection")
            return False


        return await self._check_connection(self.config, secrets) if self._check_connection else True

    def get_alert_enrichment_prompt(self) -> str:
        if self.config is None or self.config.enabled is False:
            return ""

        if not self._get_alert_enrichment_prompt:
            raise UnsupportedOperationError()
        return self._get_alert_enrichment_prompt()

    def validate_query_target(self, target_to_validate: dict[Any, Any]) -> TTarget:
        try:
            return self.query_target_type(**target_to_validate)
        except ValidationError as e:
            raise Exception(
                f"The provided query target does not have the expected structure. The validation error is: {e}"
            ) from e

    def validate_configuration(self, configuration_to_validate: dict[Any, Any], encryption_key: str | None) -> TConfig:
        try:
            return self._config_cls.model_validate(configuration_to_validate, context={ "encryption_key": encryption_key })
        except ValidationError as e:
            raise Exception(
                f"The provided configuration does not have the expected structure. The validation error is: {e}"
            ) from e

    def get_configurable_fields(self) -> List[ConfigurableConnectorField]:
        """
        Returns a list of fields (and their values) that the user can configure for this connector.
        """
        fields: list[ConfigurableConnectorField] = []
        config_dump = self.config.model_dump() if self.config else {}
        hidden_fields = self.config.hidden_fields if self.config else DEFAULT_HIDDEN_FIELDS

        for field_name in self._config_cls.model_fields:
            if field_name == "hidden_fields" or field_name in hidden_fields:
                continue

            field_type = self._config_cls.model_fields[field_name].annotation
            field_type_enum = ConfigurableConnectorFieldTypeEnum.COMPLEX
            if field_type:
                if _could_be_type(field_type=field_type, target_type=StorableSecret):
                    field_type_enum = ConfigurableConnectorFieldTypeEnum.SECRET
                elif _could_be_type(field_type=field_type, target_type=str):
                    field_type_enum = ConfigurableConnectorFieldTypeEnum.STRING
                elif _could_be_type(field_type=field_type, target_type=bool):
                    field_type_enum = ConfigurableConnectorFieldTypeEnum.BOOLEAN
                elif _could_be_type(field_type=field_type, target_type=int) or _could_be_type(field_type=field_type, target_type=float):
                    field_type_enum = ConfigurableConnectorFieldTypeEnum.NUMBER

            field_value = config_dump.get(field_name, "")
            field = ConfigurableConnectorField(field_name=field_name, field_type=field_type_enum, value=field_value)
            fields.append(field)

        return fields

    async def get_alerts(self, filter: AlertFilter) -> list[Alert]:
        """
        Retrieves the alerts that are available in the connector and assigns them priority.

        These alerts can be used to populate the central "Feed" or for further analysis
        """
        if self.config is None or self.config.enabled is False:
            return []

        if self._get_alerts is None:
            return []

        key = f"{self.id.value}-{self.user_id}-{filter.model_dump_json()}"
        if key in alerts_cache:
            return alerts_cache[key]

        secrets = await self._get_secrets()
        if secrets is None:
            logger().warning("Connector is missing token configuration, unable to provide alerts")
            return []
        alerts = await self._get_alerts(self.config, secrets, filter, self.cache)

        # Assigns priorities to the alerts based on the prioritization rules
        prioritized_alerts = await self._get_alerts_with_priorities(alerts)
        alerts_cache[key] = prioritized_alerts
        return prioritized_alerts

    async def _get_alerts_with_priorities(self, alerts: list[Alert]) -> list[Alert]:
        try:
            priority_boosts = await PrioritizationRuleManager.instance().get_prioritization_rules_async()
        except PrioritizationRuleException as e:
            logger().error("Failed to get prioritization rule boosts")
            raise e

        for alert in alerts:
            highest_mitre_priority = await EnterpriseTechniqueManager.instance().get_highest_technique_priority(
                alert.mitre_techniques
            )
            alert.assign_alert_priority(
                highest_mitre_priority,
                priority_boosts,
            )
        return alerts

    async def get_dataset_dictionary(
        self,
        path_prefix: Optional[list[str]] = None,
    ) -> list[DatasetDescription]:
        if path_prefix is None:
            path_prefix = []

        # Prefer existing data dictionary
        data_dictionary = await ddm.get_dataset_descriptions_async(connector=self.id, path_prefix=path_prefix)

        if self.config and self._merge_data_dictionary:
            secrets = await self._get_secrets()
            if secrets is None:
                logger().warning("Connector is missing token configuration, unable to provide dataset dictionary")
                return []
            return await self._merge_data_dictionary(self.config, secrets, data_dictionary, path_prefix)
        return data_dictionary

    async def upsert_dataset_descriptions(
        self, dataset_descriptions: list[UpsertDatasetDescription]
    ) -> list[DatasetDescription]:
        tasks = [
            ddm.set_dataset_description_async(
                DatasetDescription(
                    connector=self.id,
                    path=dataset_description.path,
                    description=dataset_description.description or "",
                )
            )
            for dataset_description in dataset_descriptions
        ]

        # Update dataset descriptions in parallel
        return await asyncio.gather(*tasks)

    async def generate_alert(self, alert: ConnectorGenerateAlert) -> None:
        if self.config is None or self.config.enabled is False:
            return None


        if not self._generate_alert:
            raise UnsupportedOperationError()

        secrets = await self._get_secrets()
        if secrets is None:
            logger().warning("Connector is missing token configuration, unable to generate alert")
            return None

        return await self._generate_alert(self.config, secrets, alert)

    async def delete_generated_alerts(self) -> None:
        if self.config is None or self.config.enabled is False:
            return None

        if not self._delete_generated_alerts:
            raise UnsupportedOperationError()

        secrets = await self._get_secrets()
        if secrets is None:
            logger().warning("Connector is missing token configuration, unable to delete generated alerts")
            return None

        return await self._delete_generated_alerts(self.config, secrets)

    async def get_query_target_options(self) -> ConnectorQueryTargetOptions:
        """
        Returns the query target options for this connector.

        The query target options define the shape of the dataset this connector interacts with, along with relevant field names/relationships
        The end user will rely on these options when configuring what query target they want the agent to query against
        """
        if self.config is None or self.config.enabled is False:
            UnsupportedOperationError("Connector is disabled")
        if not self._get_query_target_options or not self.config:
            return ConnectorQueryTargetOptions(selectors=[], definitions=[])

        secrets = await self._get_secrets()
        if secrets is None:
            logger().warning("Connector is missing token configuration, unable to provide query target options")
            return ConnectorQueryTargetOptions(selectors=[], definitions=[])

        return await self._get_query_target_options(self.config, secrets)

    async def get_dataset_structure_to_index(self, dataset_target: Optional[TTarget] = None) -> list[DatasetStructure]:
        """
        Returns the shape of the dataset that should be indexed for this connector.

        This will allow us to introspect the dataset structure/shape without having to reach out to the external system.
        """
        if self.config is None:
            raise UninitializedConnectorError()

        if not self._get_dataset_structure_to_index:
            return []

        secrets = await self._get_secrets()
        if secrets is None:
            logger().warning("Connector is missing token configuration, unable to provide dataset structure")
            return []

        return await self._get_dataset_structure_to_index(self.config, secrets, dataset_target)
