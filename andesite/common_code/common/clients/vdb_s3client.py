import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict, final

import boto3
from opentelemetry import trace

from common.jsonlogging.jsonlogger import Logging

logger = Logging.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class Snap(TypedDict):
    col_name: str
    date: datetime
    filename: Path | str


@final
class S3Client:
    def __init__(self, bucket_name: str) -> None:
        self.s3 = self._init_boto()
        self.bucket_name = bucket_name
        self.save_directory = Path(__file__).parent.parent.parent.joinpath("data/vecdb_snapshots")
        self.objects = self.list_objects()

    @staticmethod
    def _init_boto():
        """Initialize boto client."""
        session = boto3.Session()
        return session.client(service_name="s3")

    def list_objects(self) -> list[str] | None:
        """Retrieve list of objects in bucket.

        Returns:
            list[str]: All objects found in bucket.

        """
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name)

            objects = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    logger().info("Object Key: %s", obj["Key"])
                    objects.append(obj["Key"])

            else:
                logger().info("Bucket %s is empty.", self.bucket_name)

        except Exception:
            logger().exception("Error occured with S3 retrieval.")
            return None
        else:
            return objects

    def save_object(self, obj_key: str | Path) -> None:
        """Save specified object to local path.

        Takes in an object key a.k.a name of object and downloads
         to local file path. Specified directory is set in __init__.

        """
        local_file_path = self.save_directory.joinpath(obj_key)
        try:
            _ = self.s3.download_file(self.bucket_name, obj_key, local_file_path)
        except Exception:
            logger().exception("Error occured getting object from s3 bucket.")
        else:
            logger().info(
                "Object %s from %s bucket was saved successfully to %s",
                obj_key,
                self.bucket_name,
                self.save_directory,
            )

    def get_snapshots(self) -> None:
        """Meta function to save snapshots from s3 bucket."""

        snapshot_list = (
            [self._parse_snapshot_name(x) for x in self.objects if Path(x).suffix == ".snapshot"]
            if self.objects
            else None
        )

        collection_names = list({x["col_name"] for x in snapshot_list if x}) if snapshot_list else None

        snaps_by_collection = (
            [[snap for snap in snapshot_list if snap and snap["col_name"] == col_name] for col_name in collection_names]
            if snapshot_list and collection_names
            else None
        )
        updated_snapshots = (
            [self._find_most_recent(snapshots=col) for col in snaps_by_collection] if snaps_by_collection else None
        )

        if updated_snapshots:
            for obj in updated_snapshots:
                if obj:
                    self.save_object(obj_key=obj)

    @staticmethod
    def _parse_snapshot_name(filename: Path | str) -> Snap | None:
        """Extract collection name and generation datetime from filename.

        Args:
            filename (Path | str): Full PosixPath of snapshot or Path.name.

        Returns:
            Snap | None: dict having col_name, date, and filename as keys.

        """
        try:
            # collection name
            col_pattern = r"^([^-]+)"
            if isinstance(filename, str):
                match = re.match(col_pattern, filename)
            else:
                match = re.match(col_pattern, filename.name)

            col_name = match.group(1) if match else None

            # datetime
            date_pattern = r"-(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})\.snapshot$"
            if isinstance(filename, str):
                match = re.search(date_pattern, filename)
            else:
                match = re.search(date_pattern, filename.name)

            gen_time = datetime.strptime(match.group(1), "%Y-%m-%d-%H-%M-%S").astimezone(UTC) if match else None

        except Exception:
            logger().exception("Error in extracting datetime from snapshot title.")
            return None

        else:
            if col_name and gen_time:
                return Snap(col_name=col_name, date=gen_time, filename=filename)

            return None

    @staticmethod
    def _find_most_recent(snapshots: list[Snap]) -> Path | str:
        """Select most updated snapshot based on datetime.

        Returns:
            Path: PosixPath of most updated snapshot for given collection list.

        """
        recent_date = snapshots[0]
        for date in snapshots:
            if recent_date["date"] < date["date"]:
                recent_date = date
        return recent_date["filename"]

    def upload_snapshots(self) -> None:
        """Upload snapshots to S3.

        This function follows this process:
        - Finds all files with the .snapshot extension in the vectordb_snapshots
            directory recursively.
        - Parses each of those snapshot filenames to extract the collection name
            and date created.
        - Seperates the snapshots by collection
        - Finds the most recent snapshot version for each collection.
        - Uploads most recent snapshot version for each collection to S3 bucket.
        """
        snapshots = list(self.save_directory.glob("**/*.snapshot"))

        snapshots_parsed = [self._parse_snapshot_name(snap) for snap in snapshots]

        collection_names = list({x["col_name"] for x in snapshots_parsed if x})

        snaps_by_collection = [
            [snap for snap in snapshots_parsed if snap and snap["col_name"] == col_name]
            for col_name in collection_names
        ]

        updated_snapshots = [self._find_most_recent(snapshots=col) for col in snaps_by_collection]

        try:
            _ = [
                self.s3.upload_file(Filename=snap, Bucket=self.bucket_name, Key=snap.name)
                for snap in updated_snapshots
                if isinstance(snap, Path)
            ]
        except Exception:
            logger().exception("Error in uploading snapshots to S3.")

        else:
            logger().info("Succesfully uploaded documents: %s", updated_snapshots)
