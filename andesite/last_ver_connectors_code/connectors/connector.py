from abc import abstractmethod
import asyncio
from pathlib import Path
from typing import Any, Awaitable, Callable, Generic, List, Optional, Self, Type, TypeVar

from cachetools import TTLCache
from common.managers.user.user_manager import UsersManager
from connectors.query_instance import QueryInstance
from typing_extensions import deprecated
from pydantic import BaseModel, SecretStr
from connectors.config import ConfigurableConnectorField, ConnectorConfig
from opentelemetry import trace

from common.jsonlogging.jsonlogger import Logging
from common.managers.enterprise_technique.enterprise_technique_manager import (
    EnterpriseTechniqueManager,
)

from common.models.tool import Tool

from common.managers.prioritization_rules.prioritization_rules_manager import (
    PrioritizationRuleManager,
    PrioritizationRuleException,
)
from connectors.connector_id_enum import ConnectorIdEnum
from common.managers.dataset_descriptions.dataset_description_manager import (
    DatasetDescriptionManager,
)
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
    UpsertDatasetDescription,
)
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure
from common.models.alerts import (
    Alert,
    AlertFilter,
    ConnectorGenerateAlert,
)
from connectors.query_target_options import (
    ConnectorQueryTargetOptions,
)
from pydantic_core import ValidationError

alerts_cache: TTLCache[str, list[Alert]] = TTLCache(maxsize=10, ttl=30)

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)
ddm = DatasetDescriptionManager.instance()

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

    class Config:
        extra = "allow"

    @abstractmethod
    def get_dataset_paths(self) -> list[list[str]]:
        """
        A single connector target can point to many sets of data (e.g. multiple splunk indexes)

        Returns a list of paths that point to these datasets.

        One example use case: this will return every unique dataset that could have an associated description for a given target
        """
        pass


class ConnectorInfo(BaseModel):
    """
    This is any information that is relevant to knowing what this connector does and where it may be useful.
    """
    id: ConnectorIdEnum
    display_name: str
    available: bool
    enabled: bool
    description: str
    can_enrich_alerts: bool
    can_generate_alerts: bool
    has_alerts: bool
    has_configurable_query_target: bool
    has_indexed_data: bool
    has_user_token_management: bool
    has_dataset_descriptions: bool

TConfig = TypeVar("TConfig", bound=ConnectorConfig)
TTarget = TypeVar("TTarget", bound=ConnectorTargetInterface)

class Connector(Generic[TConfig, TTarget]):
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
        get_tools: Callable[[str, TConfig, TTarget, SecretStr | None], list[Tool]],
        check_connection: Callable[[TConfig, SecretStr | None], Awaitable[bool]] | None = None,
        get_alert_enrichment_prompt: Callable[[], str] | None = None,
        get_alerts: Callable[[TConfig, SecretStr | None, AlertFilter], Awaitable[list[Alert]]] | None = None,
        generate_alert: Callable[[TConfig, SecretStr | None, ConnectorGenerateAlert], Awaitable[None]] | None = None,
        delete_generated_alerts: Callable[[TConfig], Awaitable[None]] | None = None,
        get_does_allow_user_token_management: Callable[[TConfig], bool] | None = None,
        get_query_target_options: Callable[[TConfig], Awaitable[ConnectorQueryTargetOptions]] | None = None,
        merge_data_dictionary: Callable[[TConfig, SecretStr | None, list[DatasetDescription], list[str]], Awaitable[list[DatasetDescription]]] | None = None,
        get_dataset_structure_to_index: Callable[[TConfig, Optional[TTarget]], Awaitable[list[DatasetStructure]]] | None = None,
        UNSAFE_get_query_instance: Callable[[TConfig, SecretStr | None], QueryInstance] | None = None
    ) -> None:
        """
        :display_name: the name for this connector that will be **displayed to the end user**
        :description: a human friendly description for this connector. **This will be displayed to the end user**
        :query_target_type: a query target is how we specify what data the agent is allowed to query into. An agent can only query data explicitly allowed in the query target
        :get_tools: tools are explicitly for the agent and only the agent. Every other functionality provided by this interface is to serve the end user, but the tools are provided to the agent as its way of interacting with this connector (and thus external system)
        :check_connection: this can be optionally provided to let the user verify they have correctly configured this connector
        :get_alert_enrichment_prompt: if this connector can enrich incoming data, this prompt can be provided for the agent to know when this connector should be used to do so
        :get_alerts: if provided, this will allow alerts from this connector to be rendered in metamorph's primary "Feed" page
        :generate_alert: this allows us to send alerts to a customer's external systems
        :delete_generated_alerts: if provided, administrators will use this to clear any alerts we have generated on customers' external systems
        :get_does_allow_user_token_management: can be evaluated to see if users can manage their own token for this connector. If not provided this feature will be disabled and only global tokens will be used
        :get_query_target_options: can be called to get the query target options the user can then select from when querying this connector. The agent will respect the configured query target and only ever access datasets the user has explicitly allowed
        :merge_data_dictionary: a function that handles the merging of stored data dictionary descriptions with those that exist on external systems
        :get_dataset_structure_to_index: if a connector has a complicated data structure you can provide this function for us to index the provided dataset structure. This will allow us to inspect the external data model without having to reach out to any external systems
        """
        self.id = id
        self.display_name = display_name
        self.description = description
        self.logo_path = logo_path
        self.query_target_type = query_target_type
        self._get_tools = get_tools
        self._check_connection = check_connection
        self._get_alert_enrichment_prompt = get_alert_enrichment_prompt
        self._get_alerts = get_alerts
        self._generate_alert = generate_alert
        self._delete_generated_alerts = delete_generated_alerts
        self._get_query_target_options = get_query_target_options
        self._merge_data_dictionary = merge_data_dictionary
        self._get_does_allow_user_token_management = get_does_allow_user_token_management
        self._get_dataset_structure_to_index = get_dataset_structure_to_index
        self._get_query_instance = UNSAFE_get_query_instance

        from connectors.registry import ConnectorRegistry

        ConnectorRegistry.register(connector=self, config_cls=config_cls)


    # TODO: Load config from mongo
    async def initialize(self, config: TConfig, user_id: str | None, encryption_key: str) -> Self:
        self.config = config
        # We scope every connector to user and encryption key. then use these to derive any token internally/externally.
        self.user_id = user_id
        # Encryption key is going to be needed when storing connector configs in mongo
        self.encryption_key = encryption_key
        return self

    def get_info(self)-> ConnectorInfo:
        if self.config is None:
            raise UninitializedConnectorError()

        has_user_token_management = self._get_does_allow_user_token_management(self.config) if self._get_does_allow_user_token_management else False

        return ConnectorInfo(
            id=self.id,
            display_name=self.display_name,
            available=self.config.available,
            enabled=self.config.enabled,
            description=self.description,
            can_generate_alerts=self._generate_alert is not None,
            can_enrich_alerts=self._get_alert_enrichment_prompt is not None,
            has_alerts=self._get_alerts is not None,
            has_configurable_query_target=self._get_query_target_options is not None,
            has_indexed_data=self._get_dataset_structure_to_index is not None,
            has_user_token_management=has_user_token_management,
            has_dataset_descriptions=self._merge_data_dictionary is not None
        )



    async def get_token(self) -> SecretStr | None:
        """
        Retrieves a token to be used for authentication

        The connector must be initialized and the precedence will be as follows:
            1. use connector's global token
            2. use User's connector token

        If no token is retrieved, connectors can perform authentication at their discretion.
        e.g. the splunk connector will authenticate through oauth
        """
        if not self.config:
            raise UninitializedConnectorError()

        # Use a connector's global token if available
        if self.config.token:
            return self.config.token

        # Use the user's token if the connector allows it
        if self.config.allows_user_token_management and self.user_id is not None and self.encryption_key is not None:
            user = await UsersManager.get_user(id=self.user_id)
            if not user:
                raise ValueError("Unable to find requested user for token retrieval")
            return user.tokens.decrypt_token(
                encryption_key=self.encryption_key, token_name=ConnectorIdEnum.SPLUNK
            )

        return None

    async def get_tools(self, target: TTarget) -> list[Tool]:
        """
        Retrieves a list of tool that will be utilized by the agent.

        The agent will only be able to interact with this connector through these returned tools.
        """
        if not self.config:
            raise UninitializedConnectorError()
        return self._get_tools(self.display_name, self.config, target, await self.get_token())


    async def check_connection(self) -> bool:
        """
        Allows us to validate this connector is configured correctly and the external system can be reached
        """
        if not self.config:
            raise UninitializedConnectorError()
        return await self._check_connection(self.config, await self.get_token()) if self._check_connection else True

    def get_alert_enrichment_prompt(self) -> str:
        if not self._get_alert_enrichment_prompt:
            raise UnsupportedOperationError()
        return self._get_alert_enrichment_prompt()

    def validate_query_target(self, target_to_validate: dict[Any, Any]) -> TTarget:
        try:
            return self.query_target_type(**target_to_validate)
        except ValidationError as e:
            raise Exception(
               f"The provided query target does not have the expected structure. The validation error is: {e}"
            )

    def get_configurable_fields(self) -> List[ConfigurableConnectorField]:
        """
        Returns a list of fields (and their values) that the user can configure for this connector.
        """
        if self.config is None:
            raise UninitializedConnectorError()

        return [
            ConfigurableConnectorField(
                field_name=field_name, value=str(getattr(self.config, field_name))
            )
            for field_name in self.config.configurable_field_names
            if hasattr(self.config, field_name)
            and getattr(self.config, field_name) is not None
        ]

    async def get_alerts(self, filter: AlertFilter) -> list[Alert]:
        """
        Retrieves the alerts that are available in the connector and assigns them priority.

        These alerts can be used to populate the central "Feed" or for further analysis
        """
        if self.config is None:
            raise UninitializedConnectorError()

        if self._get_alerts is None:
            return []

        key = f"{self.id.value}-{self.user_id}-{filter.model_dump_json()}"
        if key in alerts_cache:
            return alerts_cache[key]

        alerts = await self._get_alerts(
            self.config,
            await self.get_token(),
            filter
        )

        # Assigns priorities to the alerts based on the prioritization rules
        try:
            priority_boosts = await PrioritizationRuleManager.instance().get_prioritization_rules_async()
        except PrioritizationRuleException as e:
            logger().error("Failed to get prioritization rule boosts")
            raise e

        for alert in alerts:
            highest_mitre_priority = await EnterpriseTechniqueManager.instance().get_highest_technique_priority(alert.mitre_techniques)
            alert.assign_alert_priority(
                highest_mitre_priority,
                priority_boosts,
            )
        alerts_cache[key] = alerts
        return alerts

    async def get_dataset_dictionary(
        self,
        path_prefix: Optional[list[str]] = [],
    ) -> list[DatasetDescription]:
        if path_prefix is None:
            path_prefix = []

        # Prefer existing data dictionary
        data_dictionary = await ddm.get_dataset_descriptions_async(
            connector=self.id, path_prefix=path_prefix
        )

        if self.config and self._merge_data_dictionary:
            return await self._merge_data_dictionary(self.config, await self.get_token(), data_dictionary, path_prefix)
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
        if self.config is None:
            raise UninitializedConnectorError()

        if not self._generate_alert:
            raise UnsupportedOperationError()

        return await self._generate_alert(self.config, await self.get_token(), alert)

    async def delete_generated_alerts(self) -> None:
        if self.config is None:
            raise UninitializedConnectorError()

        if not self._delete_generated_alerts:
            raise UnsupportedOperationError()

        return await self._delete_generated_alerts(self.config)

    async def get_query_target_options(self) -> ConnectorQueryTargetOptions:
        """
        Returns the query target options for this connector.

        The query target options define the shape of the dataset this connector interacts with, along with relevant field names/relationships
        The end user will rely on these options when configuring what query target they want the agent to query against
        """
        if not self._get_query_target_options or not self.config:
            return ConnectorQueryTargetOptions(selectors=[], definitions=[])

        return await self._get_query_target_options(self.config)

    async def get_dataset_structure_to_index(
        self, dataset_target: Optional[TTarget] = None
    ) -> list[DatasetStructure]:
        """
        Returns the shape of the dataset that should be indexed for this connector.

        This will allow us to introspect the dataset structure/shape without having to reach out to the external system.
        """
        if self.config is None:
            raise UninitializedConnectorError()

        if not self._get_dataset_structure_to_index:
            return []

        return await self._get_dataset_structure_to_index(self.config, dataset_target)

    @deprecated("If you need the query instance of a connector, try to abstract the functionality into the connector framework itself")
    async def UNSAFE_get_query_instance(self) -> QueryInstance:
        """
        DO NOT USE THIS. This is solely to support legacy behavior and no new call sites should be added
        """
        if self.config is None:
            raise UninitializedConnectorError()

        if self._get_query_instance is None:
            raise UnsupportedOperationError()

        return self._get_query_instance(self.config, await self.get_token())
