from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GroupOut(ORMModel):
    id: int
    slug: str
    label: str
    color: str


class UserOut(ORMModel):
    id: int
    display_name: str
    initials: str


# --- Events ---------------------------------------------------------------

class EventBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    venue: str | None = None
    starts_at: datetime
    ends_at: datetime
    tentative: bool = False
    group_id: int | None = None  # null = private (self-only)


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = None
    venue: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    tentative: bool | None = None
    group_id: int | None = None


class EventOut(ORMModel):
    id: int
    title: str
    venue: str | None
    starts_at: datetime
    ends_at: datetime
    tentative: bool
    owner: UserOut
    group: GroupOut | None


# --- Feed -----------------------------------------------------------------

class FeedItem(BaseModel):
    """One row in the 'What's happening' feed."""

    event: EventOut
    is_mine: bool
    my_rsvp: str | None  # "going" | "interested" | "declined" | None


class FeedDay(BaseModel):
    """A day-bucket in the feed (Today / Tomorrow / Sat May 2)."""

    date: str           # ISO yyyy-mm-dd
    label: str          # "Today", "Tomorrow", or weekday name
    note: str           # "Thu, Apr 30"
    items: list[FeedItem]
