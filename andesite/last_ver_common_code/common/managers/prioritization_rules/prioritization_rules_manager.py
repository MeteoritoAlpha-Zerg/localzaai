from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection

from typing import Any, Optional, Set

from pymongo import ASCENDING
from opentelemetry import trace
import pymongo
import asyncio
from pathlib import Path
import json


from common.jsonlogging.jsonlogger import Logging
from common.managers.prioritization_rules.prioritization_rules_model import (
    PrioritizationRule,
)


logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class PrioritizationRuleException(Exception):
    """Base class for exceptions in this module."""

    pass


class PrioritizationRuleManager:
    def __init__(
        self,
    ):
        """
        Initializes the PrioritizationRuleManager.

        :return: None
        """
        self._storage_collection: Optional[AgnosticCollection] = None
        self._loaded_paths: Set[str] = set()
        self._initial_rules: list[PrioritizationRule] = []

    # TODO: remove this when a better solution is created for PR deployments
    async def load_initial_rules_async(self, path: Path, reload: bool = False):
        if not path.exists() or not path.is_dir():
            logger().error(
                f'Default rule path "{path}" does not exist or is not a directory'
            )
            raise PrioritizationRuleException(
                f'Default rule path "{path}" does not exist'
            )

        if not reload and str(path) in self._loaded_paths:
            logger().info(
                f"Path '{path}' already loaded and reload is False. Skipping load."
            )
            return

        for file in path.glob("*.json"):
            try:
                with open(file, "r") as f:
                    descriptions = json.load(f)
                    for description in descriptions:
                        description_object = PrioritizationRule.model_validate(
                            description,
                        )
                        self._initial_rules.append(description_object)
            except Exception as e:
                logger().error(f"Unexpected error: {str(e)}")
                continue

        self._loaded_paths.add(str(path))

    def load_initial_rules(self, path: Path, reload: bool = False):
        """
        Synchronously loads default prioritization rules from the given path. The function will look for all json files in the path
        (non recurisvely), and attempt to load a Prompt model for each file. The next call to `initialize` will perform
        the synchronization.

        :param path: The path on disk where prioritization rules are present with JSON extensions.
        :param reload: Whether to reload from the path even if it has been loaded before. Default is False.
        :return: None
        """
        return self._get_event_loop().run_until_complete(
            self.load_initial_rules_async(path, reload)
        )

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "PrioritizationRuleManager":
        """
        Get a global singleton of the PrioritizationRuleManager in a threadsafe manner.
        :return: The app-wide PrioritizationRuleManager singleton.
        """
        return PrioritizationRuleManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("get_prioritization_rule_async")
    async def get_prioritization_rule_async(
        self,
        rule_name: str,
    ) -> Optional[PrioritizationRule]:
        """
        Asynchronously retrieves prioritization rule from the database or cache.

        :param rule_name: The rule's name.
        :return: The retrieved prioritization rule.
        :raises PrioritizationRuleException: If the prioritization rule is not found.
        """
        if self._storage_collection is None:
            raise PrioritizationRuleException(
                "Unable to get prioritization rule because no storage collection was initialized."
            )
        rule = await self._storage_collection.find_one(
            {
                "rule_name": rule_name,
            }
        )  # type: ignore[func-returns-value]

        if rule is None:
            return None

        logger().info(
            "Retrieved prioritization rule with name '%s'",
            rule_name,
        )

        return PrioritizationRule.from_mongo(rule)

    @tracer.start_as_current_span("delete_prioritization_rules_async")
    async def delete_prioritization_rules_async(self, rule_names: list[str]):
        """
        Asynchronously deletes the content of a prioritization rule in the database.

        :param rule_names: a list of rule names to delete.
        :raises PrioritizationRuleException: If there is an error deleting from the prioritization rule.
        """
        if self._storage_collection is None:
            raise PrioritizationRuleException(
                f"Unable to delete prioritization rule with names {rule_names} because no storage collection was initialized."
            )

        delete_result = await self._storage_collection.delete_many(
            {"rule_name": {"$in": rule_names}}
        )

        logger().info(
            "Deleted %d prioritization rules with rule_names '%s'",
            delete_result.deleted_count,
            rule_names,
        )

    @tracer.start_as_current_span("get_prioritization_rules_async")
    async def get_prioritization_rules_async(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[PrioritizationRule]:
        """
        Asynchronously gets the content of prioritization rules.

        :raises PrioritizationRuleException: If there is an error getting from the prioritization rule.
        """
        if self._storage_collection is None:
            raise PrioritizationRuleException(
                "Unable to get prioritization rules because no storage collection was initialized."
            )

        pipeline: list[dict[str, Any]] = []
        if skip:
            pipeline.append({"$skip": skip})
        if limit:
            pipeline.append({"$limit": limit})

        rule_documents = await self._storage_collection.aggregate(pipeline).to_list(  # type: ignore
            length=None
        )
        if not rule_documents:
            return []

        rules = []
        for doc in rule_documents:
            task_metadata_response = PrioritizationRule.from_mongo(doc)
            if task_metadata_response:
                rules.append(task_metadata_response)

        return rules

    @tracer.start_as_current_span("insert_prioritization_rule_async")
    async def insert_prioritization_rule_async(
        self, rule: PrioritizationRule
    ) -> PrioritizationRule:
        """
        Asynchronously sets the content of a prioritization rule in the database without overriding any.
        You can introduce new tasks using this method.

        :param task_metadata: The prioritization rule.
        :return: The updated prioritization rule.
        :raises PrioritizationRuleException: If there is an error setting the prioritization rule.
        """
        if self._storage_collection is None:
            raise PrioritizationRuleException(
                f"Unable to set prioritization rule with name '{rule.rule_name}' because no storage collection was initialized."
            )
        try:
            insert_result = await self._storage_collection.insert_one(
                rule.to_mongo(),
            )  # type: ignore[var-annotated]

            if insert_result.inserted_id is None:
                raise PrioritizationRuleException(
                    f"Unable to insert rule with name '{rule.rule_name}'"
                )

            logger().info(
                "prioritization rule with with name '%s' was updated",
                rule.rule_name,
            )
            return rule
        except pymongo.errors.DuplicateKeyError:
            raise PrioritizationRuleException(
                f"Unable to insert rule with name '{rule.rule_name}' as it already exists"
            )
        except Exception as e:
            logger().error(
                f"An error occurred while setting prioritization rule with name '{rule.rule_name}': {e}"
            )
            raise e

    @tracer.start_as_current_span("upsert_prioritization_rule_async")
    async def upsert_prioritization_rule_async(
        self, rule: PrioritizationRule
    ) -> PrioritizationRule:
        """
        Asynchronously sets the content of a prioritization rule in the database. You can
        update prioritization rules and introduce new tasks using this method.

        :param task_metadata: The prioritization rule.
        :return: The updated prioritization rule.
        :raises PrioritizationRuleException: If there is an error setting the prioritization rule.
        """
        if self._storage_collection is None:
            raise PrioritizationRuleException(
                f"Unable to set prioritization rule with name '{rule.rule_name}' because no storage collection was initialized."
            )
        try:
            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {
                    "rule_name": rule.rule_name,
                },
                {"$set": rule.to_mongo()},
                upsert=True,
                return_document=True,
            )  # type: ignore[var-annotated]

            updated_rule = PrioritizationRule.from_mongo(updated_mongo_document)
            if updated_rule is None:
                raise PrioritizationRuleException(
                    f"Unable to update document with name '{rule.rule_name}'"
                )

            logger().info(
                "prioritization rule with with name '%s' was updated",
                rule.rule_name,
            )
            return updated_rule
        except Exception as e:
            logger().error(
                f"An error occurred while setting prioritization rule with name '{rule.rule_name}': {e}"
            )
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: Optional[AgnosticCollection] = None):
        """
        Initializes the PrioritizationRuleManager with a storage collection.

        :param storage_collection: The storage collection to use.
        :return: None
        """
        if self._storage_collection is not None:
            logger().warning(
                "PrioritizationRuleManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "PrioritizationRuleManager initialized without a storage collection - prioritization rules will not be persisted"
            )
            return
        await self._storage_collection.create_index(
            [("rule_name", ASCENDING)],
            unique=True,
        )

        for rule in self._initial_rules:
            try:
                await self.insert_prioritization_rule_async(rule)
            except PrioritizationRuleException:
                # we don't log exec_info here because this is normal part of loading backend up
                # if something doesn't insert, it's likely because it already exists
                # and if it's not that, failure here is not blocking
                logger().info(
                    f"Rule with name '{rule.rule_name}' already loaded in",
                )

    @staticmethod
    def _get_event_loop():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
