import uuid
from functools import lru_cache
from typing import Any

from celery import Celery  # type: ignore [import-untyped]
from pydantic_settings import BaseSettings

from common.clients.redis_client import RedisConfig
from common.jsonlogging.jsonlogger import Logging
from common.managers.task_metadata.task_metadata_manager import (
    TaskMetadataException,
    TaskMetadataManager,
)
from common.managers.task_metadata.task_metadata_model import (
    TaskMetadata,
    TaskStatusEnum,
)
from common.utils.context import get_message_attributes_from_context

"""
This module is responsible for managing the Celery clients used by the application.
It provides a way to initialize the clients with the appropriate configuration.
"""
logger = Logging.get_logger(__name__)


class CeleryConfig(BaseSettings):
    task_queue_name: str = "processor"
    redis_cfg: RedisConfig = RedisConfig()


class CeleryException(Exception):
    pass


CELERY_LOWEST_PRIORITY = 9
CELERY_HIGHEST_PRIORITY = 0

DOC_PROCESSING_TASK = "process_document"
CREATE_ALERT_GROUPS_TASK = "create_alert_groups"
UPDATE_STRUCTURES_TASK = "update_structures"
ENRICH_ALERTS_TASK = "enrich_alerts"
ENRICH_ALERT_GROUPS_TASK = "enrich_alert_groups"
ENRICH_DATASET_DESCRIPTIONS_TASK = "enrich_dataset_descriptions"


class CeleryClient:
    _celery_app: Celery | None

    def initialize(self, cfg: CeleryConfig):
        self._celery_app = Celery(cfg.task_queue_name, broker=cfg.redis_cfg.redis_url)

    def __init__(
        self,
        cfg: CeleryConfig | None = None,
    ):
        """
        Initializes the CeleryClient.

        :return: None
        """
        if cfg is None:
            cfg = CeleryConfig()
        self._config = cfg
        self._celery_app = Celery(cfg.task_queue_name, broker=cfg.redis_cfg.redis_url)

    @classmethod
    @lru_cache(maxsize=1)
    def instance(cls) -> "CeleryClient":
        """
        Get a global singleton of the CeleryClient in a threadsafe manner.
        :return: The app-wide CeleryClient singleton.
        """
        return CeleryClient()  # type: ignore[call-arg]

    def get_celery_app(self) -> Celery:
        if not self._celery_app:
            raise ValueError("CeleryClient is not initialized.")
        return self._celery_app

    async def cancel_tasks(
        self,
        name: str,
        kwargs: dict[str, Any],
        incomplete_match: bool = True,
        exclude_task_ids: list[str] | None = None,
    ) -> None:
        """
        Cancel tasks in Celery.

        Args:
            name (str): The name of the matching tasks to cancel.
            kwargs (dict[str, Any]): A dictionary containing the arguments to the task.
            incomplete_match (bool): If True, will match tasks with the same name and
                                        partial arguments. If False, will match tasks with the same name
                                        and exact arguments.
            exclude_task_ids (list[str], optional): A list of task IDs to exclude from cancellation.

        Raises:
            ValueError: If the CeleryClient is not initialized.
            CeleryException: If there is an error canceling the task.
        """
        if not self._celery_app:
            raise ValueError("CeleryClient is not initialized.")

        logger().info(
            f"Canceling tasks with name: {name} and args: {kwargs} with incomplete matching set to {incomplete_match} and excluding task ids: {exclude_task_ids}"
        )

        matching_tasks = await TaskMetadataManager.instance().get_task_metadatas_async(
            matching_statuses=[TaskStatusEnum.PENDING, TaskStatusEnum.STARTED],
            task_name=name,
            args=kwargs,
            incomplete_match_args=incomplete_match,
        )
        logger().info(f"Found matching tasks: {[matching_task.task_id for matching_task in matching_tasks]}")
        if exclude_task_ids:
            matching_tasks = [task for task in matching_tasks if task.task_id not in exclude_task_ids]
        try:
            for matching_task in matching_tasks:
                self._celery_app.control.revoke(matching_task.task_id, terminate=True)
                logger().info(
                    f"Cancelled task {matching_task.task_id} with name: {matching_task.task_name} and args: {matching_task.args}"
                )
        except Exception as err:
            logger().exception("Failed to cancel task in Celery")
            raise CeleryException("Failed to cancel task in Celery") from err

    async def send_task(self, name: str, kwargs: dict[str, Any], priority: int = CELERY_LOWEST_PRIORITY) -> None:
        """
        Send a task to Celery.

        Args:
            name (str): The name of the task to send.
            kwargs (dict[str, Any]): A dictionary containing the arguments to the task.
                                     Note that kwargs cannot contain a key called
                                     'message_attributes', as that is used to carry
                                     request context.
            priority (int, optional): The priority of the task. Defaults to 9.
                                      Valid options between 0 and 9, with 0 being highest priority.

        Raises:
            ValueError: If the CeleryClient is not initialized.
            CeleryException: If 'message_attributes' is passed as a task argument.
            CeleryException: If there is an error saving task metadata.
            CeleryException: If there is an error sending the task to Celery.
            CeleryException: If priority is not in valid range.
        """
        if not self._celery_app:
            raise ValueError("CeleryClient is not initialized.")
        if "message_attributes" in kwargs:
            raise CeleryException("message_attributes cannot be passed as a task argument.")
        if priority < CELERY_HIGHEST_PRIORITY or priority > CELERY_LOWEST_PRIORITY:
            raise CeleryException(
                f"priority must be an int between {CELERY_HIGHEST_PRIORITY} and {CELERY_LOWEST_PRIORITY}"
            )

        task_id = str(uuid.uuid4())
        try:
            task_metadata = TaskMetadata(
                task_id=task_id,
                task_name=name,
                args=kwargs,
            )
            await TaskMetadataManager.instance().upsert_task_metadata_async(task_metadata)
        except TaskMetadataException as e:
            raise CeleryException("Failed to send task to Celery, could not save task metadata") from e
        try:
            kwargs["message_attributes"] = get_message_attributes_from_context()
            self._celery_app.send_task(name, task_id=task_id, kwargs=kwargs, priority=priority)
            logger().info(f"Sent task with id: {task_id} and priority {priority}")
        except Exception as err:
            logger().exception("Failed to send task to Celery:")
            raise CeleryException("Failed to send task to Celery") from err
