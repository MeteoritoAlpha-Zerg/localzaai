import asyncio
from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorCollection as AgnosticCollection

from typing import Any, Optional

from pymongo import ASCENDING, ReturnDocument
from opentelemetry import trace

from common.jsonlogging.jsonlogger import Logging
from common.managers.dataset_structures.dataset_structure_model import DatasetStructure

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class DatasetStructureException(Exception):
    """Base class for exceptions in this module."""

    pass


class DatasetStructureManager:
    def __init__(
        self,
    ):
        """
        Initializes the DatasetStructureManager.

        :return: None
        """
        self._storage_collection: Optional[AgnosticCollection] = None

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "DatasetStructureManager":
        """
        Get a global singleton of the DatasetStructureManager in a threadsafe manner.
        :return: The app-wide DatasetStructureManager singleton.
        """
        return DatasetStructureManager()  # type: ignore[call-arg]

    @tracer.start_as_current_span("get_dataset_structure_async")
    async def get_dataset_structure_async(
        self,
        connector: str,
        dataset: str,
    ) -> Optional[DatasetStructure]:
        """
        Asynchronously retrieves dataset structure from the database.

        :param connector: The connector of the dataset.
        :param dataset: The dataset.
        :return: The retrieved dataset structure.
        :raises DatasetStructureException: If the dataset structure is not found.
        """
        if self._storage_collection is None:
            raise DatasetStructureException(
                "Unable to get dataset structure because no storage collection was initialized."
            )
        dataset_structure = await self._storage_collection.find_one(
            {
                "connector": connector,
                "dataset": dataset,
            }
        )  # type: ignore[func-returns-value]

        if dataset_structure is None:
            return None

        logger().info(
            "Retrieved dataset structure with connector '%s' and dataset '%s'",
            connector,
            dataset,
        )

        return DatasetStructure.from_mongo(dataset_structure)

    @tracer.start_as_current_span("get_all_dataset_structures_async")
    async def get_all_dataset_structures_async(
        self, connector: str
    ) -> list[DatasetStructure]:
        if self._storage_collection is None:
            raise DatasetStructureException(
                "Unable to get dataset structure because no storage collection was initialized."
            )
        pipeline: list[dict[str, Any]] = [
            {"$match": {"connector": connector}},
        ]

        # to_list with length of None means it will return ALL results
        dataset_structures = await self._storage_collection.aggregate(pipeline).to_list(  # type: ignore
            length=None
        )

        structures: list[DatasetStructure] = []
        for structure in dataset_structures:
            structure_response = DatasetStructure.from_mongo(structure)
            if structure_response:
                structures.append(structure_response)
        return structures

    @tracer.start_as_current_span("get_dataset_structure")
    def get_dataset_structure(
        self, connector: str, dataset: str
    ) -> list[DatasetStructure]:
        """
        Synchronously retrieves dataset structure from the database.

        :param connector: The connector of the dataset.
        :param dataset: The dataset.
        :return: The retrieved dataset structure.
        :raises DatasetStructureException: If the dataset structure is not found.
        """
        dataset_structure = self._get_event_loop().run_until_complete(
            self.get_dataset_structure_async(connector, dataset)
        )
        return dataset_structure

    @tracer.start_as_current_span("delete_dataset_structures_async")
    async def delete_dataset_structures_async(
        self, connector: str, datasets: list[str]
    ):
        """
        Asynchronously deletes the content of a dataset structure in the database.

        :param connector: The connector of the dataset.
        :param dataset: The dataset.
        :param dataset: The dataset.
        :raises DatasetStructureException: If there is an error deleting from the dataset structure.
        """
        if self._storage_collection is None:
            raise DatasetStructureException(
                f"Unable to delete dataset structures with connector '{connector}' and datasets '{datasets}' because no storage collection was initialized."
            )

        delete_result = await self._storage_collection.delete_many(
            {"connector": connector, "dataset": {"$in": datasets}}
        )

        logger().info(
            "Deleted %d dataset structures with connector '%s': '%s'",
            delete_result.deleted_count,
            connector,
            datasets,
        )

    @tracer.start_as_current_span("set_dataset_structure_async")
    async def set_dataset_structure_async(
        self, dataset_structure: DatasetStructure
    ) -> DatasetStructure:
        """
        Asynchronously sets the content of a dataset structure in the database. You can
        update dataset structures and introduce new structures using this method.

        :param dataset_structure: The dataset structure.
        :return: The updated dataset structure.
        :raises DatasetStructureException: If there is an error setting the dataset structure.
        """
        if self._storage_collection is None:
            raise DatasetStructureException(
                f"Unable to set dataset structure with connector '{dataset_structure.connector}' and dataset '{dataset_structure.dataset}' because no storage collection was initialized."
            )
        try:
            upserted_document: dict = (
                await self._storage_collection.find_one_and_update(
                    filter={
                        "connector": dataset_structure.connector,
                        "dataset": dataset_structure.dataset,
                    },
                    update={"$set": dataset_structure.to_mongo()},
                    upsert=True,
                    return_document=ReturnDocument.AFTER,
                )
            )  # type: ignore[func-returns-value]
            logger().info(
                "Dataset structure with connector '%s' and dataset '%s' was updated",
                dataset_structure.connector,
                dataset_structure.dataset,
            )
            return DatasetStructure.from_mongo(upserted_document)  # type: ignore
        except Exception as e:
            logger().error(
                f"An error occurred while setting dataset structure with connector '{dataset_structure.connector}' and dataset '{dataset_structure.dataset}': {e}"
            )
            raise e

    @tracer.start_as_current_span("initialize")
    async def initialize(self, storage_collection: Optional[AgnosticCollection] = None):
        """
        Initializes the DatasetStructureManager with a storage collection.

        :param storage_collection: The storage collection to use.
        :return: None
        """
        if self._storage_collection is not None:
            logger().warning(
                "DatasetStructureManager is already initialized - calling initialize multiple times has no effect"
            )
            return

        self._storage_collection = storage_collection
        if self._storage_collection is None:
            logger().warning(
                "DatasetStructureManager initialized without a storage collection - dataset structures will not be persisted"
            )
            return
        await self._storage_collection.create_index([("connector", ASCENDING)])
        await self._storage_collection.create_index(
            [("connector", ASCENDING), ("dataset", ASCENDING)],
            unique=True,
        )

    @staticmethod
    def _get_event_loop():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
