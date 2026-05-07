# Porch backend

FastAPI + SQLAlchemy + SQLite backend for the Porch social-calendar app.

## Quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create the SQLite DB and load demo data matching the frontend mockup
python -m app.seed

# Run the API + frontend
uvicorn app.main:app --reload --port 8000
```

Open <http://localhost:8000>. The login modal appears first; sign in with the
demo account printed by the seed:

- **email:** `grace@porch.local`
- **password:** `porchporch`

API docs at <http://localhost:8000/docs>.

## What's implemented

| Area              | Status                                         |
| ----------------- | ---------------------------------------------- |
| Auth              | signup / login / logout / me (session cookie)  |
| Events CRUD       | list (with date range + group filter), create, get, update, delete |
| Feed              | day-bucketed, filterable by friend-group slug  |
| RSVPs             | upsert (PUT) and clear (DELETE) per event      |
| Porch presence    | broadcast / list / end                         |
| Friends           | list                                           |
| Friend groups     | list                                           |
| Notifications     | Stub (501)                                     |

## Architecture notes

- **Friend groups are owner-scoped.** Each user has their own buckets ("close",
  "gym", …) — these are *my* labels for *my* friends.
- **Event visibility.** An event is visible to user U if it is owned by U, or
  if its `group_id` belongs to a `FriendGroup` that lists U as a member via a
  `Friendship` row. So Jake creating a "Pilates" event in *his* gym group makes
  it visible to everyone in his gym group, including Grace.
- **Auth.** Cookie-based session via Starlette's `SessionMiddleware`, signed
  with `PORCH_SECRET` (override the default before any deploy). Passwords
  hashed with bcrypt. Replace with OAuth/magic-link when ready.
- **Same-origin frontend.** `Porch.html` is served at `/` so cookies "just
  work" without CORS gymnastics.

## Tweak the demo

Re-run `python -m app.seed` any time to reset the database to the mockup state
relative to *today's* week (events shift forward as time passes).

## Layout

```
backend/
├── app/
│   ├── main.py            FastAPI app, middleware, static frontend
│   ├── database.py        SQLAlchemy engine + Session
│   ├── deps.py            current_user dependency (reads session cookie)
│   ├── security.py        bcrypt + session secret
│   ├── models.py          User, FriendGroup, Friendship, Event, Rsvp, PorchPresence, Notification
│   ├── schemas.py         Pydantic request/response shapes
│   ├── seed.py            Demo data loader
│   └── routers/
│       ├── auth.py
│       ├── events.py
│       ├── feed.py
│       ├── friends.py
│       ├── groups.py
│       ├── rsvps.py
│       ├── presence.py
│       └── notifications.py
├── porch.db               SQLite (gitignored)
└── requirements.txt
```
