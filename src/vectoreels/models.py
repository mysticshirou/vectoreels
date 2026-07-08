from typing import Any

from pydantic import BaseModel, Field


class SimpleLabelValue(BaseModel):
    label: str
    value: str
    href: str | None = None


class GroupedLabelValue(BaseModel):
    title: str
    items: list["GroupedLabelValue | SimpleLabelValue"] = Field(alias="dict")


class LikedPost(BaseModel):
    timestamp: int
    media: list[Any] = Field(default_factory=list)
    label_values: list[SimpleLabelValue | GroupedLabelValue]
    fbid: str
