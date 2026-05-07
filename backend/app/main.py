from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import models  # noqa: F401  (registers tables on Base.metadata)
from .database import Base, engine
from .routers import auth, events, feed, friends, groups, notifications, presence, rsvps
from .security import SESSION_COOKIE, SESSION_SECRET

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Porch",
    description="Backend for Porch — a social calendar for friend groups.",
    version="0.1.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie=SESSION_COOKIE,
    same_site="lax",
    https_only=False,  # Set True behind HTTPS in production.
    max_age=60 * 60 * 24 * 30,  # 30 days
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(feed.router)
app.include_router(friends.router)
app.include_router(groups.router)
app.include_router(rsvps.router)
app.include_router(presence.router)
app.include_router(notifications.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# --- Static frontend ------------------------------------------------------
# Serve frontend/Porch.html at /, and any sibling static assets at /static.
# Same-origin keeps session cookies simple.
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(FRONTEND_DIR / "Porch.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
