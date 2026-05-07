from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import current_user

router = APIRouter(prefix="/presence", tags=["presence"])


class PorchIn(BaseModel):
    location: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=280)
    visibility: models.PresenceVisibility = models.PresenceVisibility.everyone
    group_id: int | None = None
    duration_minutes: int = Field(default=120, ge=15, le=720)


class PorchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: schemas.UserOut
    location: str | None
    note: str | None
    visibility: models.PresenceVisibility
    group: schemas.GroupOut | None
    starts_at: datetime
    expires_at: datetime


def _to_out(db: Session, p: models.PorchPresence) -> PorchOut:
    user = db.get(models.User, p.user_id)
    group = db.get(models.FriendGroup, p.group_id) if p.group_id else None
    return PorchOut(
        id=p.id,
        user=schemas.UserOut.model_validate(user),
        location=p.location,
        note=p.note,
        visibility=p.visibility,
        group=schemas.GroupOut.model_validate(group) if group else None,
        starts_at=p.starts_at,
        expires_at=p.expires_at,
    )


@router.post("/porch", response_model=PorchOut, status_code=status.HTTP_201_CREATED)
def im_on_the_porch(
    payload: PorchIn,
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    """Broadcast that I'm around. Replaces any existing active broadcast from me."""
    if payload.visibility == models.PresenceVisibility.group:
        if payload.group_id is None:
            raise HTTPException(status_code=400, detail="group_id required when visibility=group.")
        group = db.get(models.FriendGroup, payload.group_id)
        if group is None or group.owner_id != me.id:
            raise HTTPException(status_code=400, detail="Unknown friend group.")

    now = datetime.utcnow()
    # End any of my still-active broadcasts before starting a new one.
    db.query(models.PorchPresence).filter(
        models.PorchPresence.user_id == me.id,
        models.PorchPresence.expires_at > now,
    ).update({models.PorchPresence.expires_at: now}, synchronize_session=False)

    presence = models.PorchPresence(
        user_id=me.id,
        location=payload.location,
        note=payload.note,
        visibility=payload.visibility,
        group_id=payload.group_id if payload.visibility == models.PresenceVisibility.group else None,
        starts_at=now,
        expires_at=now + timedelta(minutes=payload.duration_minutes),
    )
    db.add(presence)
    db.commit()
    db.refresh(presence)
    return _to_out(db, presence)


@router.get("/porch", response_model=list[PorchOut])
def list_porch_presence(
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    """Active broadcasts from friends I'm allowed to see, plus my own."""
    now = datetime.utcnow()

    # Friend ids = users in any of *my* friend groups.
    friend_ids_subq = select(models.Friendship.friend_id).where(
        models.Friendship.owner_id == me.id
    )
    # Group ids in which *I* am a member (so visibility=group broadcasts are visible to me).
    my_member_groups_subq = select(models.Friendship.group_id).where(
        models.Friendship.friend_id == me.id
    )

    rows = (
        db.query(models.PorchPresence)
        .filter(models.PorchPresence.expires_at > now)
        .filter(
            (models.PorchPresence.user_id == me.id)
            | (
                models.PorchPresence.user_id.in_(friend_ids_subq)
                & (
                    (models.PorchPresence.visibility == models.PresenceVisibility.everyone)
                    | (models.PorchPresence.group_id.in_(my_member_groups_subq))
                )
            )
        )
        .order_by(models.PorchPresence.starts_at.desc())
        .all()
    )
    return [_to_out(db, r) for r in rows]


@router.delete("/porch", status_code=status.HTTP_204_NO_CONTENT)
def end_my_porch(
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    now = datetime.utcnow()
    db.query(models.PorchPresence).filter(
        models.PorchPresence.user_id == me.id,
        models.PorchPresence.expires_at > now,
    ).update({models.PorchPresence.expires_at: now}, synchronize_session=False)
    db.commit()
