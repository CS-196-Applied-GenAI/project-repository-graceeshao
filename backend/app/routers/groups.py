from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import current_user

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[schemas.GroupOut])
def list_groups(
    db: Session = Depends(get_db),
    me: models.User = Depends(current_user),
):
    return (
        db.query(models.FriendGroup)
        .filter(models.FriendGroup.owner_id == me.id)
        .order_by(models.FriendGroup.id)
        .all()
    )
