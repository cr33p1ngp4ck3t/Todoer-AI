"""Validate AI output before it becomes an editable task draft."""

from datetime import datetime, timezone
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


class SmartParseRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(min_length=1, max_length=4000)
    reference_time: AwareDatetime | None = None
    timezone: str = Field(default="UTC", min_length=1, max_length=100)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Use a valid IANA timezone") from exc
        return value


class DraftFields(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    priority: Literal["low", "medium", "high"] = "medium"
    tags: list[
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
        ]
    ] = Field(default_factory=list, max_length=20)
    due_date: AwareDatetime | None = None
    recurrence: Literal["daily", "weekly", "monthly"] | None = None

    @field_validator("tags")
    @classmethod
    def normalized_tags(cls, value):
        return list(dict.fromkeys(tag.lower() for tag in value))

    @field_validator("due_date")
    @classmethod
    def utc_deadline(cls, value: datetime | None):
        return value.astimezone(timezone.utc) if value else None

    @model_validator(mode="after")
    def recurrence_has_deadline(self):
        if self.recurrence and self.due_date is None:
            raise ValueError("A recurring draft requires a deadline")
        return self


class TaskDraft(DraftFields):
    recurrence_timezone: str = "UTC"
    source: Literal["ai", "fallback"]
    warnings: list[str] = Field(default_factory=list)
