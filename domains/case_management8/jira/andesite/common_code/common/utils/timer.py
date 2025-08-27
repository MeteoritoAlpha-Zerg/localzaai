from datetime import UTC, datetime

from pydantic import BaseModel, Field, computed_field


class AccessClock(BaseModel):
    start_time: datetime = Field(exclude=True, default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = Field(exclude=True, default=None)

    @computed_field  # type: ignore[misc]
    @property
    def total_seconds(self) -> float | None:
        if self.end_time is not None:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def stop_clock(self):
        self.end_time = datetime.now(UTC)


class TotalAccess(AccessClock):
    # TODO: downstream dependencies should be added here (ex. splunk query, a call to an api, etc.)
    dependencies: dict[str, AccessClock] = Field(default={})

    def add_dependency(self, key: str):
        dependency = AccessClock()
        self.dependencies[key] = dependency

    def stop_clock_dependency(self, key: str):
        if key in self.dependencies:
            self.dependencies[key].stop_clock()
