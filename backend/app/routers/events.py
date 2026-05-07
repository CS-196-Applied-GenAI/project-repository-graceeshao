from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..deps import current_user

router = APIRouter(prefix="/events", tags=["events"])


def _verify_group_owned(db: Session, owner_id: int, group_id: int | None):
    """Reject group_ids that don't belong to the requesting user."""
    if group_id is None:
        return
    group = db.get(models.FriendGroup, group_id)
    if group is None or group.owner_id != owner_id:
        raise HTTPException(status_code=400, detail="Unknown friend group.")


@router.get("", response_model=list[schemas.EventOut])
def list_events(
    start: datetime = Query(..., description="Inclusive lower bound on starts_at"),
    end: datetime = Query(..., description="Exclusive upper bound on starts_at"),
    group_id: int | None = Query(None, description="Filter to a single friend group"),
    include_friends: bool = Query(
        True,
        description="Include events from friends visible via shared groups",
    ),
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    """Events visible to the current user inside [start, end).

    Always includes the user's own events. When include_friends is true,
    also includes events shared by friends through any FriendGroup that
    has the current user as a member.
    """
    q = db.query(models.Event).options(
        joinedload(models.Event.owner),
        joinedload(models.Event.group),
    )

    visible_filter = models.Event.owner_id == me.id
    if include_friends:
        visible_group_ids = select(models.Friendship.group_id).where(
            models.Friendship.friend_id == me.id
        )
        visible_filter = or_(
            visible_filter,
            models.Event.group_id.in_(visible_group_ids),
        )

    q = q.filter(visible_filter)
    q = q.filter(models.Event.starts_at >= start, models.Event.starts_at < end)

    if group_id is not None:
        q = q.filter(models.Event.group_id == group_id)

    return q.order_by(models.Event.starts_at).all()


@router.post("", response_model=schemas.EventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: schemas.EventCreate,
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=400, detail="ends_at must be after starts_at.")
    _verify_group_owned(db, me.id, payload.group_id)

    event = models.Event(owner_id=me.id, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    event = (
        db.query(models.Event)
        .options(joinedload(models.Event.owner), joinedload(models.Event.group))
        .filter(models.Event.id == event_id)
        .first()
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")
    if event.owner_id != me.id and not _is_visible_to(db, event, me.id):
        raise HTTPException(status_code=404, detail="Event not found.")
    return event


@router.patch("/{event_id}", response_model=schemas.EventOut)
def update_event(
    event_id: int,
    payload: schemas.EventUpdate,
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    event = db.get(models.Event, event_id)
    if event is None or event.owner_id != me.id:
        raise HTTPException(status_code=404, detail="Event not found.")

    data = payload.model_dump(exclude_unset=True)
    if "group_id" in data:
        _verify_group_owned(db, me.id, data["group_id"])

    for key, val in data.items():
        setattr(event, key, val)

    if event.ends_at <= event.starts_at:
        raise HTTPException(status_code=400, detail="ends_at must be after starts_at.")

    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    event = db.get(models.Event, event_id)
    if event is None or event.owner_id != me.id:
        raise HTTPException(status_code=404, detail="Event not found.")
    db.delete(event)
    db.commit()


def _is_visible_to(db: Session, event: models.Event, user_id: int) -> bool:
    if event.group_id is None:
        return False
    return (
        db.query(models.Friendship.id)
        .filter(
            models.Friendship.group_id == event.group_id,
            models.Friendship.friend_id == user_id,
        )
        .first()
        is not None
    )
