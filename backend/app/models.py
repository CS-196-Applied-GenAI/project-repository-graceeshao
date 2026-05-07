from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class RsvpStatus(str, Enum):
    going = "going"
    interested = "interested"
    declined = "declined"


class PresenceVisibility(str, Enum):
    everyone = "everyone"
    group = "group"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String)
    initials: Mapped[str] = mapped_column(String(4))
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    groups: Mapped[list["FriendGroup"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    events: Mapped[list["Event"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class FriendGroup(Base):
    """A bucket the owner sorts friends into (e.g. "Gym crew", "Close")."""

    __tablename__ = "friend_groups"
    __table_args__ = (UniqueConstraint("owner_id", "slug", name="uq_group_owner_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    slug: Mapped[str] = mapped_column(String, index=True)  # "close", "gym", ...
    label: Mapped[str] = mapped_column(String)             # "Close", "Gym crew"
    color: Mapped[str] = mapped_column(String)             # hex e.g. "#B8623A"

    owner: Mapped[User] = relationship(back_populates="groups")
    memberships: Mapped[list["Friendship"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class Friendship(Base):
    """Links the owner to another user, tagging the friend with a group."""

    __tablename__ = "friendships"
    __table_args__ = (
        UniqueConstraint("owner_id", "friend_id", "group_id", name="uq_friendship"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("friend_groups.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    friend: Mapped[User] = relationship(foreign_keys=[friend_id])
    group: Mapped[FriendGroup] = relationship(back_populates="memberships")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Visibility scope: which of the owner's friend groups can see this event.
    # Null means "self only" (the user's own private calendar item).
    group_id: Mapped[int | None] = mapped_column(ForeignKey("friend_groups.id"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String)
    venue: Mapped[str | None] = mapped_column(String, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    tentative: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped[User] = relationship(back_populates="events")
    group: Mapped[FriendGroup | None] = relationship()
    rsvps: Mapped[list["Rsvp"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Rsvp(Base):
    __tablename__ = "rsvps"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_rsvp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[RsvpStatus] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event: Mapped[Event] = relationship(back_populates="rsvps")
    user: Mapped[User] = relationship()


class PorchPresence(Base):
    """Ephemeral 'I'm on the porch' broadcast — expires after a few hours."""

    __tablename__ = "porch_presence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    visibility: Mapped[PresenceVisibility] = mapped_column(String, default=PresenceVisibility.everyone)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("friend_groups.id"), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String)        # "rsvp", "porch", "invite", ...
    title: Mapped[str] = mapped_column(String)
    body: Mapped[str | None] = mapped_column(String, nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
