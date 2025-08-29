from typing import Annotated

from croniter import croniter  # type: ignore [import-untyped]
from pydantic import AfterValidator, BaseModel


def validate_cron_expression(value: str) -> str:
    try:
        if not croniter.is_valid(value):
            raise ValueError(f"Invalid cron expression: {value}")
        return value
    except Exception:
        raise ValueError(f"Invalid cron expression: {value}")


CronExpression = Annotated[str, AfterValidator(validate_cron_expression)]


class CronConfig(BaseModel):
    cron_expression: CronExpression

    @property
    def minute(self) -> str:
        return self.cron_expression.split()[0]

    @property
    def hour(self) -> str:
        return self.cron_expression.split()[1]

    @property
    def day_of_month(self) -> str:
        return self.cron_expression.split()[2]

    @property
    def month_of_year(self) -> str:
        return self.cron_expression.split()[3]

    @property
    def day_of_week(self) -> str:
        return self.cron_expression.split()[4]
