from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", status_code=501)
def list_notifications():
    raise HTTPException(status_code=501, detail="Not implemented yet.")


@router.post("/{notification_id}/read", status_code=501)
def mark_read(notification_id: int):
    raise HTTPException(status_code=501, detail="Not implemented yet.")
