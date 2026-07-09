from typing import Any

from pydantic import BaseModel, Field

STAGE_CLEANED = 1
STAGE_TITLED = 2
STAGE_EMBEDDED = 3


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


class ProcessedPost(BaseModel):
    fbid: str = Field(min_length=1)
    timestamp: int
    url: str = Field(min_length=1)
    caption: str | None
    hashtags: list[str]
    music_title: str | None = None
    audio_embedding: list[float] | None = None
    stage: int = STAGE_CLEANED


class SearchFilters(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    description: str | None = None
    song: str | None = None
    date_from: int | None = None
    date_to: int | None = None
    audio_embedding: list[float] | None = None
