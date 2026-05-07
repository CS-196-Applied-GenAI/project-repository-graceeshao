[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/9yS33qEc)

# Porch

A social calendar for friend groups. Friends share events bucketed by group
("Close", "Gym crew", "Work", "College"), RSVP to each other's plans, and
broadcast "I'm on the porch" when they're free to hang.

## Layout

```
.
├── frontend/Porch.html       Single-file UI (HTML + inline CSS/JS)
├── backend/                  FastAPI + SQLAlchemy + SQLite
│   ├── app/                  Routers, models, schemas, seed
│   └── requirements.txt
├── render.yaml               One-click Render deploy config
├── spec.md                   Project spec
└── spec_2ndidea.md           Second-idea spec
```

The FastAPI app serves the HTML at `/` so frontend + API share an origin.

## Run locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000  (sign in: grace@porch.local / porchporch)
```

See `backend/README.md` for the full backend write-up (architecture, endpoints,
visibility model).

## Deploy to Render (free tier)

The repo includes a `render.yaml` blueprint, so deployment is one-click:

1. Push this repo to GitHub.
2. Sign in at <https://render.com> (you can use GitHub OAuth).
3. **New** → **Blueprint** → connect this repo. Render reads `render.yaml`,
   provisions a free Python web service, and starts the build.
4. First build takes 5–10 minutes. Once it goes green, the URL appears at the
   top of the service page (something like `https://porch-xxxx.onrender.com`).

The blueprint sets these env vars automatically:

| Var                 | Why                                                  |
| ------------------- | ---------------------------------------------------- |
| `PORCH_SECRET`      | Random per-deploy session signing key                |
| `PORCH_PRODUCTION`  | Turns on HTTPS-only cookies                          |
| `PORCH_AUTOSEED`    | Re-seeds demo data when the DB is empty (cold boots) |
| `PYTHON_VERSION`    | Pins to 3.11.7                                       |

### Free-tier caveats

- **Sleeps after ~15 min idle.** Cold start is ~30 seconds. After that, the
  app stays warm as long as it's getting requests.
- **Ephemeral disk.** SQLite resets on every cold boot. The auto-seed on
  startup keeps the demo data (Grace + her friends + this week's events)
  always present. Real signups made between cold boots will not persist —
  that's fine for a demo, but plan to swap in Render Postgres for real users.
- **Demo login** is the same as local: `grace@porch.local` / `porchporch`.

## Tech

FastAPI · SQLAlchemy 2 · SQLite · Pydantic · bcrypt · Starlette
SessionMiddleware · vanilla JS frontend (no build step).
