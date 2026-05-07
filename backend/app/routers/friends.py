from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..deps import current_user

router = APIRouter(prefix="/friends", tags=["friends"])


@router.get("", response_model=list[schemas.UserOut])
def list_friends(
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    rows = (
        db.query(models.Friendship)
        .options(joinedload(models.Friendship.friend))
        .filter(models.Friendship.owner_id == me.id)
        .all()
    )
    seen: dict[int, models.User] = {}
    for r in rows:
        seen.setdefault(r.friend_id, r.friend)
    return list(seen.values())
