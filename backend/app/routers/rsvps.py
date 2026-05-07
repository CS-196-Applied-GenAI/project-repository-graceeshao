from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import current_user
from ..routers.events import _is_visible_to

router = APIRouter(prefix="/rsvps", tags=["rsvps"])


class RsvpIn(BaseModel):
    status: models.RsvpStatus


class RsvpOut(BaseModel):
    event_id: int
    status: models.RsvpStatus


@router.put("/{event_id}", response_model=RsvpOut)
def upsert_rsvp(
    event_id: int,
    payload: RsvpIn,
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    event = db.get(models.Event, event_id)
    if event is None or (event.owner_id != me.id and not _is_visible_to(db, event, me.id)):
        raise HTTPException(status_code=404, detail="Event not found.")
    if event.owner_id == me.id:
        raise HTTPException(status_code=400, detail="You can't RSVP to your own event.")

    rsvp = (
        db.query(models.Rsvp)
        .filter(models.Rsvp.event_id == event_id, models.Rsvp.user_id == me.id)
        .first()
    )
    if rsvp is None:
        rsvp = models.Rsvp(event_id=event_id, user_id=me.id, status=payload.status)
        db.add(rsvp)
    else:
        rsvp.status = payload.status
        rsvp.updated_at = datetime.utcnow()

    db.commit()
    return RsvpOut(event_id=event_id, status=payload.status)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def clear_rsvp(
    event_id: int,
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    rsvp = (
        db.query(models.Rsvp)
        .filter(models.Rsvp.event_id == event_id, models.Rsvp.user_id == me.id)
        .first()
    )
    if rsvp is not None:
        db.delete(rsvp)
        db.commit()
