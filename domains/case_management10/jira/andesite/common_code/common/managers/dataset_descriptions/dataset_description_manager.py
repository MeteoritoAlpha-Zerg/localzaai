import asyncio
import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection
from opentelemetry import trace
from pymongo import ASCENDING, ReturnDocument

from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_descriptions.dataset_description_model import (
    DatasetDescription,
)
from common.models.connector_id_enum import ConnectorIdEnum

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class DatasetDescriptionException(Exception):
    """Base class for exceptions in this module."""

    pass


class DatasetDescriptionManager:
    def __init__(
        self,
    ):
        """
        Initializes the DatasetDescriptionManager.

        :return: None
        """
        self._storage_collection: AgnosticCollection | None = None
        self._loaded_paths: set[str] = set()
        self._initial_descriptions: list[DatasetDescription] = []

    def check_client_initialization(function: Any):
        def check_client(self, *args, **kwargs):
            if self._storage_collection is None:
                raise DatasetDescriptionException("No storage collection initialized")
            return function(self, *args, **kwargs)

        return check_client

    async def load_initial_descriptions_async(self, path: Path):
        """
        Loads default dataset descriptions from the given path. The function will look for all csv files in the path
        (non recursively), and attempt to load a Prompt model for each row in the files. The next call to `initialize` will perform
        the synchronization.

        :param path: The path on disk where dataset descriptions are present with csv extensions.
        :return: None
        """
        if not path.exists() or not path.is_dir():
            logger().error(f'Default dataset description path "{path}" does not exist or is not a directory')
            raise DatasetDescriptionException(f'Default prompt path "{path}" does not exist')

        if str(path) in self._loaded_paths:
            logger().info(f"Path '{path}' already loaded. Skipping load.")
            return

        for file in path.glob("*.csv"):
            try:
                with open(file) as f:
                    descriptions_reader = csv.reader(f)
                    # Skip the header row
                    next(descriptions_reader, None)
                    for description in descriptions_reader:
                        description_object = DatasetDescription(
                            connector=ConnectorIdEnum(description[0]),
                            path=DatasetDescription.string_to_path(description[1]),
                            description=description[2],
                        )
                        self._initial_descriptions.append(description_object)
            except Exception as e:
                logger().error("Encountered error when loading initial data dictionary", exc_info=e)
                continue

        self._loaded_paths.add(str(path))

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "DatasetDescriptionManager":
        """
        Get a global singleton of the DatasetDescriptionManager in a threadsafe manner.
        :return: The app-wide DatasetDescriptionManager singleton.
        """
        return DatasetDescriptionManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("get_dataset_descriptions_async")
    @check_client_initialization
    async def get_dataset_descriptions_async(
        self,
        connector: str,
        path_prefix: list[str] | None = None,
        skip: int | None = None,
        limit: int | None = None,
        exact_path: bool = False,
    ) -> list[DatasetDescription]:
        """
        Asynchronously retrieves dataset descriptions from the database.

        :param connector: The connector of the dataset.
        :return: The retrieved dataset descriptions.
        :raises DatasetDescriptionException: If the dataset description is not found.
        """
        if path_prefix is None:
            path_prefix = []
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "connector": connector,
                    **(
                        {"path": path_prefix}
                        if exact_path
                        else DatasetDescription.path_to_mongo_filter(path_prefix if path_prefix else [])
                    ),
                }
            },
            {
                "$sort": {
                    "connector": ASCENDING,
                    "path": ASCENDING,
                }
            },
        ]

        if skip is not None:
            pipeline.append({"$skip": skip})

        if limit is not None:
            pipeline.append({"$limit": limit})

        # WARNING: to_list with length of None means it will return ALL results
        dataset_descriptions = await self._storage_collection.aggregate(  # type: ignore
            pipeline
        ).to_list(length=None)
        if dataset_descriptions is None:
            raise DatasetDescriptionException(
                f"Dataset descriptions for '{connector}' / '{path_prefix}' does not exist"
            )
        response: list[DatasetDescription] = []
        for dataset_description in dataset_descriptions:
            dataset_description_response = DatasetDescription.from_mongo(dataset_description)
            if dataset_description_response:
                response.append(dataset_description_response)

        logger().debug(
            "Retrieved dataset description with connector '%s', path prefix '%s'",
            connector,
            path_prefix,
        )

        return response

    @tracer.start_as_current_span("get_dataset_descriptions")
    def get_dataset_descriptions(
        self, connector: str, path_prefix: list[str] | None = None
    ) -> list[DatasetDescription]:
        """
        Synchronously retrieves dataset descriptions from the database.

        :param connector: The connector of the dataset.
        :return: The retrieved dataset description.
        :raises DatasetDescriptionException: If the dataset description is not found.
        """
        if path_prefix is None:
            path_prefix = []
        dataset_descriptions: list[DatasetDescription] = self._get_event_loop().run_until_complete(
            self.get_dataset_descriptions_async(connector=connector, path_prefix=path_prefix)
        )
        return dataset_descriptions

    @tracer.start_as_current_span("delete_dataset_description_async")
    @check_client_initialization
    async def delete_dataset_description_async(
        self,
        connector: str,
        path: list[str],
    ) -> None:
        """
        Asynchronously deletes the content of a dataset description in the database.

        :param connector: The connector of the dataset.
        :param path: The path of the dataset description we'd like to delete.
        :raises DatasetDescriptionException: If there is an error deleting from the dataset description.
        """
        await self._storage_collection.delete_one(  # type: ignore
            {"connector": connector, "path": path}
        )

    @tracer.start_as_current_span("set_dataset_description_async")
    @check_client_initialization
    async def set_dataset_description_async(self, description: DatasetDescription) -> DatasetDescription:
        """
        Asynchronously sets the content of a dataset description in the database. You can
        update dataset descriptions and introduce new descriptions using this method.

        :param dataset_description: The dataset description.
        :return: The updated dataset description.
        :raises DatasetDescriptionException: If there is an error setting the dataset description.
        """
        try:
            upserted_document = await self._storage_collection.find_one_and_update(  # type: ignore
                filter={
                    "connector": description.connector,
                    "path": description.path,
                },
                update={"$set": description.to_mongo()},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            logger().info(
                "Dataset description with connector '%s' / path '%s' was updated",
                description.connector,
                description.path,
            )
            # find_one_and_update raises an Exception if there is an issue, therefore upserted_document cannot be None
            return DatasetDescription.from_mongo(  # type: ignore
                upserted_document
            )
        except Exception as e:
            logger().error(
                f"An error occurred while setting dataset description with connector '{description.connector}' / path '{description.path}': {e}"
            )
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: AgnosticCollection | None = None) -> None:
        """
        Initializes the DatasetDescriptionManager with a storage collection.

        :param storage_collection: The storage collection to use.
        :return: None
        """
        if self._storage_collection is not None:
            logger().warning(
                "DatasetDescriptionManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "DatasetDescriptionManager initialized without a storage collection - dataset descriptions will not be persisted"
            )
            return
        await self._storage_collection.create_index(
            [
                ("connector", ASCENDING),
                ("path", ASCENDING),
            ]
        )

        for description in self._initial_descriptions:
            document = await self._storage_collection.find_one(  # type: ignore[func-returns-value]
                {"connector": description.connector, "path": description.path}
            )
            if document is None:
                await self._storage_collection.insert_one(description.to_mongo())
            else:
                logger().info(
                    "Dataset description with connector '%s' and path '%s' already loaded",
                    description.connector,
                    description.path,
                )

    @staticmethod
    def _get_event_loop():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
