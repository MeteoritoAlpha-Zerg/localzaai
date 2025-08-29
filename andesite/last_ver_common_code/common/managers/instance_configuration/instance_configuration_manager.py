import asyncio
from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection

from typing import Optional

import pymongo
from pymongo import ASCENDING
from opentelemetry import trace


from common.jsonlogging.jsonlogger import Logging
from common.managers.instance_configuration.instance_configuration_model import (
    InstanceConfigurationSetting,
    InstanceConfigurationSettingEnum,
)


logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class InstanceConfigurationException(Exception):
    """Base class for exceptions in this module."""

    pass


default_settings: dict[
    InstanceConfigurationSettingEnum, InstanceConfigurationSetting
] = {
    InstanceConfigurationSettingEnum.CHAT_TTL: InstanceConfigurationSetting(
        setting_name=InstanceConfigurationSettingEnum.CHAT_TTL, setting_value=172600
    ),
    InstanceConfigurationSettingEnum.DOC_PROCESSOR_MAX_QUESTIONS: InstanceConfigurationSetting(
        setting_name=InstanceConfigurationSettingEnum.DOC_PROCESSOR_MAX_QUESTIONS,
        setting_value=15,
    ),
    InstanceConfigurationSettingEnum.DOC_PROCESSOR_LOOKBACK_PERIOD_IN_DAYS: InstanceConfigurationSetting(
        setting_name=InstanceConfigurationSettingEnum.DOC_PROCESSOR_LOOKBACK_PERIOD_IN_DAYS,
        setting_value=2,
    ),
}


class InstanceConfigurationManager:
    def __init__(
        self,
    ) -> None:
        """
        Initializes the InstanceConfigurationManager.

        :return: None
        """
        self._storage_collection: Optional[AgnosticCollection] = None

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "InstanceConfigurationManager":
        """
        Get a global singleton of the InstanceConfigurationManager in a threadsafe manner.
        :return: The app-wide InstanceConfigurationManager singleton.
        """
        return InstanceConfigurationManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("get_configuration_setting")
    def get_configuration_setting(
        self,
        setting_name: InstanceConfigurationSettingEnum,
    ) -> InstanceConfigurationSetting:
        """
        Synchronously retrieves instance configuration setting from the database or cache.

        :param setting_name: The setting's name.
        :return: The retrieved instance configuration setting.
        :raises InstanceConfigurationException: If the instance configuration setting is not found.
        """
        return self._get_event_loop().run_until_complete(
            self.get_configuration_setting_async(setting_name=setting_name)
        )

    @tracer.start_as_current_span("get_configuration_setting_async")
    async def get_configuration_setting_async(
        self,
        setting_name: InstanceConfigurationSettingEnum,
    ) -> InstanceConfigurationSetting:
        """
        Asynchronously retrieves instance configuration setting from the database or cache.

        :param setting_name: The setting's name.
        :return: The retrieved instance configuration setting.
        :raises InstanceConfigurationException: If the instance configuration setting is not found.
        """
        if self._storage_collection is None:
            raise InstanceConfigurationException(
                "Unable to get instance configuration setting because no storage collection was initialized."
            )
        rule = await self._storage_collection.find_one(
            {
                "setting_name": setting_name,
            }
        )  # type: ignore[func-returns-value]

        if rule is None:
            logger().debug(
                "Instance configuration setting with name '%s' not found in the database - returning default",
                setting_name,
            )
            default_setting = default_settings.get(setting_name)
            if not default_setting:
                raise InstanceConfigurationException(
                    f"Instance configuration setting with name '{setting_name}' not found in the database or default settings"
                )
            return default_setting

        logger().info(
            "Retrieved instance configuration setting with name '%s'",
            setting_name,
        )

        return InstanceConfigurationSetting.from_mongo(rule)

    @tracer.start_as_current_span("upsert_configuration_setting_async")
    async def upsert_configuration_setting_async(
        self, setting: InstanceConfigurationSetting
    ) -> InstanceConfigurationSetting:
        """
        Asynchronously sets the content of a instance configuration setting in the database. You can
        update instance configuration settings and introduce new tasks using this method.

        :param task_metadata: The instance configuration setting.
        :return: The updated instance configuration setting.
        :raises InstanceConfigurationException: If there is an error setting the instance configuration setting.
        """
        if self._storage_collection is None:
            raise InstanceConfigurationException(
                f"Unable to set instance configuration setting with name '{setting.setting_name}' because no storage collection was initialized."
            )
        try:
            updated_mongo_document = await self._storage_collection.find_one_and_update(
                {
                    "setting_name": setting.setting_name,
                },
                {"$set": setting.to_mongo()},
                upsert=True,
                return_document=True,
            )  # type: ignore[var-annotated]

            updated_rule = InstanceConfigurationSetting.from_mongo(
                updated_mongo_document
            )
            if updated_rule is None:
                raise InstanceConfigurationException(
                    f"Unable to update document with name '{setting.setting_name}'"
                )

            logger().info(
                "instance configuration setting with with name '%s' was updated",
                setting.setting_name,
            )
            return updated_rule
        except Exception as e:
            logger().error(
                f"An error occurred while setting instance configuration setting with name '{setting.setting_name}': {e}"
            )
            raise e

    @tracer.start_as_current_span("insert_prioritization_rule_async")
    async def insert_configuration_setting_async(
        self, setting: InstanceConfigurationSetting
    ) -> InstanceConfigurationSetting:
        """
        Asynchronously sets the content of an instance setting in the database without overriding any.
        You can introduce new tasks using this method.

        :param task_metadata: The instance setting.
        :return: The updated instance setting.
        :raises InstanceConfigurationException: If there is an error setting the instance setting.
        """
        if self._storage_collection is None:
            raise InstanceConfigurationException(
                f"Unable to set instance setting with name '{setting.setting_name}' because no storage collection was initialized."
            )
        try:
            insert_result = await self._storage_collection.insert_one(
                setting.to_mongo(),
            )  # type: ignore[var-annotated]

            if insert_result.inserted_id is None:
                raise InstanceConfigurationException(
                    f"Unable to insert setting with name '{setting.setting_name}'"
                )

            logger().info(
                "instance setting with with name '%s' was updated",
                setting.setting_name,
            )
            return setting
        except pymongo.errors.DuplicateKeyError:
            raise InstanceConfigurationException(
                f"Unable to insert rule with name '{setting.setting_name}' as it already exists"
            )
        except Exception as e:
            logger().error(
                f"An error occurred while setting instance setting with name '{setting.setting_name}': {e}"
            )
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: Optional[AgnosticCollection] = None):
        """
        Initializes the InstanceConfigurationManager with a storage collection.

        :param storage_collection: The storage collection to use.
        :return: None
        """
        missing_settings = set(InstanceConfigurationSettingEnum) - set(
            default_settings.keys()
        )
        if missing_settings:
            raise ValueError(f"Missing default settings for: {missing_settings}")

        if self._storage_collection is not None:
            logger().warning(
                "InstanceConfigurationManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "InstanceConfigurationManager initialized without a storage collection - instance configuration settings will not be persisted"
            )
            return
        await self._storage_collection.create_index(
            [("setting_name", ASCENDING)],
            unique=True,
        )

        for setting in default_settings.values():
            try:
                await self.insert_configuration_setting_async(setting)
            except InstanceConfigurationException:
                # we don't log exec_info here because this is normal part of loading backend up
                # if something doesn't insert, it's likely because it already exists
                # and if it's not that, failure here is not blocking
                logger().info(
                    f"Setting with name '{setting.setting_name}' already loaded in",
                )

    @staticmethod
    def _get_event_loop():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
