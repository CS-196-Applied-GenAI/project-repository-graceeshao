from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..deps import current_user

router = APIRouter(prefix="/feed", tags=["feed"])


def _day_label(d: date, today: date) -> str:
    delta = (d - today).days
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    return d.strftime("%A")


def _day_note(d: date) -> str:
    return d.strftime("%a, %b %-d") if hasattr(d, "strftime") else d.isoformat()


@router.get("", response_model=list[schemas.FeedDay])
def get_feed(
    days: int = Query(7, ge=1, le=30, description="How many days forward to include"),
    group_slug: str | None = Query(None, description="Filter to a friend-group slug, e.g. 'gym'"),
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    """The 'What's happening' feed: friends' visible events grouped by day.

    Excludes events the current user already owns *unless* group_slug is "self".
    The frontend renders the user's own items in the calendar; the feed is
    primarily about what friends are up to.
    """
    today = datetime.now().date()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=days)

    visible_group_ids_subq = select(models.Friendship.group_id).where(
        models.Friendship.friend_id == me.id
    )

    q = (
        db.query(models.Event)
        .options(joinedload(models.Event.owner), joinedload(models.Event.group))
        .filter(models.Event.starts_at >= start, models.Event.starts_at < end)
    )

    if group_slug == "self":
        q = q.filter(models.Event.owner_id == me.id)
    else:
        q = q.filter(
            or_(
                models.Event.owner_id == me.id,
                models.Event.group_id.in_(visible_group_ids_subq),
            )
        )
        if group_slug:
            # "Show events from friends I've classified into <slug>." We resolve
            # the slug via *my* friend groups, then filter to events owned by
            # the friends inside that group.
            my_group = (
                db.query(models.FriendGroup)
                .filter(
                    models.FriendGroup.owner_id == me.id,
                    models.FriendGroup.slug == group_slug,
                )
                .first()
            )
            if my_group is None:
                return []
            friend_ids_subq = select(models.Friendship.friend_id).where(
                models.Friendship.group_id == my_group.id
            )
            q = q.filter(models.Event.owner_id.in_(friend_ids_subq))

    events = q.order_by(models.Event.starts_at).all()

    # My RSVPs for these events, fetched once.
    rsvp_map: dict[int, str] = {}
    if events:
        rsvp_map = {
            r.event_id: r.status
            for r in db.query(models.Rsvp).filter(
                models.Rsvp.user_id == me.id,
                models.Rsvp.event_id.in_([e.id for e in events]),
            )
        }

    by_day: dict[date, list[schemas.FeedItem]] = defaultdict(list)
    for e in events:
        by_day[e.starts_at.date()].append(
            schemas.FeedItem(
                event=schemas.EventOut.model_validate(e),
                is_mine=(e.owner_id == me.id),
                my_rsvp=rsvp_map.get(e.id),
            )
        )

    return [
        schemas.FeedDay(
            date=d.isoformat(),
            label=_day_label(d, today),
            note=_day_note(d),
            items=items,
        )
        for d, items in sorted(by_day.items())
    ]
