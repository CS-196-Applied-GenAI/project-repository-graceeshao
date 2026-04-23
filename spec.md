# NU Events — Product & Engineering Specification

**Project:** Northwestern Campus Events Aggregator
**Repo:** `graceeshao/nu-events`
**Live:** [nu-events.vercel.app](https://nu-events.vercel.app/)
**Date:** April 23, 2026

---

## 1. Overview

NU Events is a campus events aggregator that scrapes events from multiple sources across Northwestern University, normalizes them into a unified schema, and surfaces them through a filterable web frontend. This spec covers enhancements to the existing working system: personalization, analytics, automation, frontend improvements, and new source expansion.

---

## 2. Current Architecture

### 2.1 Data Flow

```
Mac scraper → local SQLite → sync script → Render Postgres → FastAPI → Vercel (Next.js)
```

- **Scraper runtime:** Python, runs locally on Mac
- **Local DB:** SQLite (`nu_events.db`) — scraper writes here first
- **Remote DB:** Postgres on Render (`oregon-postgres.render.com`)
- **Sync:** `sync_to_remote.py` pushes future events from SQLite → Render Postgres after each scrape run
- **Backend API:** FastAPI (REST), exposes `/events`, `/events/{id}`, `/organizations`
- **Frontend:** Next.js on Vercel, reads from FastAPI via `NEXT_PUBLIC_API_URL`

### 2.2 LLM Infrastructure

- **Model:** Google Gemma 3 12B (`gemma3:12b`) via Ollama
- **Host:** Local Mac at `http://localhost:11434`
- **Fallback models available:** `gemma3:4b`, `gemma3:1b`
- **Usage:** Event extraction from Instagram captions and email bodies; batch pre-classification for emails
- **Config:** `ollama_url` is a config variable — swappable to a remote Ollama instance or API-based model (OpenAI/Anthropic) with no code changes

### 2.3 Shared Event Schema (Postgres)

| Field        | Type     | Notes                                               |
|-------------|----------|-----------------------------------------------------|
| title       | string   | Event name                                          |
| date        | date     | Event date                                          |
| start_time  | time     | Start time (nullable)                               |
| end_time    | time     | End time (nullable)                                 |
| location    | string   | Venue / room                                        |
| description | text     | Full description                                    |
| category    | enum     | Academic, Arts, Sports, Social, Career, Other       |
| rsvp_url    | string   | Link to RSVP or event page (nullable)               |
| free_food   | boolean  | Detected via keyword matching                       |
| source      | string   | Origin source identifier (planit_purple, instagram, email, dept_website) |
| org_id      | FK       | Link to organization record (nullable)              |

### 2.4 State Management

- **Scrape cursor:** `scrape_state.json` tracks rotation position for Instagram (cycles through ~377 orgs, ~15 per run) and last-poll timestamp for email ingestion

---

## 3. Existing Sources (Built & Running)

### 3.1 PlanIt Purple (Primary Source)

- **Method:** HTML scraping with BeautifulSoup
- **Target:** `planitpurple.northwestern.edu`
- **Pagination:** Up to 5 pages of event listings
- **Detail fetch:** Optional per-event detail page scrape (`fetch_details=True`) for descriptions and RSVP links
- **Category mapping:** PlanIt Purple tags → internal enum (Academic, Arts, Sports, Social, Career, Other)
- **Free food detection:** Keyword matching on description text
- **Output:** ~200+ events per run
- **Fragility note:** CSS selector-dependent (`article.event`, `.event-date`, `.time-location`). Will break if Northwestern redesigns the page. Selectors should be documented and easy to update.
- **Status:** ✅ Fully built, tested, running

### 3.2 Instagram (Club Accounts)

- **Method:** Custom HTTP scraper using `requests.Session` with exported Chrome cookies (`ig_cookies.json`). Hits Instagram's internal feed endpoints directly — not Instaloader, not the official API, not Apify.
- **Scale:** ~377 active org accounts with Instagram handles
- **Rotation:** Cursor-based — scrapes ~15 orgs per run, rotates through all 377 across multiple runs (tracked in `scrape_state.json`)
- **Pipeline:**
  1. Fetch recent posts from each org's profile
  2. Regex pre-filter (`instagram_prefilter.py`) screens captions for date/time/event keywords — skips ~70% of posts before LLM
  3. Surviving posts → Ollama (Gemma 3 12B) for structured event extraction
  4. Deduplication + persist to database
- **Cookie dependency:** Relies on manually exported browser cookies. These expire and need periodic refresh.
- **Status:** ✅ Built, tested, running

### 3.3 Email Newsletters

- **Method:** Gmail API + OAuth2 → IMAP connection
- **Source:** All listserv emails auto-labeled `NU-Events` via Gmail filters (filter matches listserv sender addresses)
- **Pipeline:**
  1. **Fetch:** Connect via IMAP with OAuth2, read from `NU-Events` label, search for messages since last poll (timestamp in `scrape_state.json`)
  2. **Dedup:** Check `Message-ID` against `IngestedEmail` records in Postgres
  3. **Batch pre-classify:** Send batches of 20 email subject+body pairs to Ollama — classify as `EVENT` vs `NOT_EVENT` before expensive extraction
  4. **LLM extraction:** `parse_event_with_llm()` per email, with regex fallback (`email_parser.py`) on LLM failure
  5. **Persist:** Save extracted events + `IngestedEmail` audit record to Postgres
- **Multi-event handling:** Emails (e.g., weekly digests) can contain multiple events — LLM prompt asks for a list of events, not a single one
- **Status:** ✅ Built, tested, running

---

## 4. Planned Sources (Not Yet Built)

### 4.1 Department Websites

- **Approach:** Cherry-pick 10-15 high-value departments with targeted scrapers per site
- **Target departments (initial list):**
  - Computer Science
  - SESP (School of Education & Social Policy)
  - Weinberg College of Arts & Sciences
  - Kellogg School of Management
  - McCormick School of Engineering
  - Bienen School of Music
  - Medill School of Journalism
  - School of Communication
  - Pritzker School of Law
  - Northwestern Libraries
  - (5 more TBD based on event volume / student demand)
- **Method:** Per-department scraper using BeautifulSoup or similar. Each department has its own page structure / CMS, so each scraper will need custom CSS selectors.
- **Extraction:** Route through the same Ollama pipeline for unstructured event pages; use direct HTML parsing for well-structured ones
- **Priority:** Low (ranked #5) — build after personalization, analytics, and automation are in place

---

## 5. New Feature: Personalization (Priority #1)

### 5.1 User Authentication

- **Method:** Email/password authentication
- **No SSO:** Not integrating with Northwestern NetID (requires IT approval)
- **Storage:** User accounts table in Render Postgres
- **Session management:** JWT or session tokens via FastAPI

### 5.2 User Profile & Preferences

#### 5.2.1 Explicit Preferences (Onboarding)

On first login, users go through a lightweight onboarding flow:

- **Category selection:** Pick interested categories (Academic, Arts, Sports, Social, Career, Other) — multi-select
- **Org following:** Option to follow specific organizations from the org directory
- **Preferences stored in:** `user_preferences` table linked to user account

#### 5.2.2 Implicit Preference Learning

Track user behavior to refine recommendations over time:

- **Signals to capture:**
  - Event clicks (viewed detail page)
  - Event saves/bookmarks
  - RSVP link clicks
  - Org profile views
  - Time spent on event detail pages (optional, frontend-tracked)
- **Storage:** `user_activity` table logging (user_id, event_id, action_type, timestamp)

### 5.3 Recommendation Engine

- **Approach:** LLM-powered via Ollama (same infrastructure as scraping)
- **Method:**
  1. Generate embeddings for each event (title + description + category) using Ollama
  2. Build a user preference vector from explicit preferences + implicit activity history
  3. Similarity matching (cosine similarity) between user vector and event embeddings
  4. Rank and surface top-N recommended events in a personalized feed
- **Cold start:** Explicit onboarding preferences provide initial signal before behavioral data accumulates
- **Refresh cadence:** Recompute recommendations on each login or periodically (TBD — could be daily batch or on-demand)
- **Endpoint:** `GET /recommendations?user_id=X` on FastAPI

### 5.4 Personalized Feed

- **Default view for logged-in users:** Shows recommended events first, then all events
- **Logged-out users:** See the current global feed (no change)
- **Saved/bookmarked events:** Accessible via a "My Events" section in the UI

---

## 6. New Feature: Analytics & Data Tracking (Priority #2)

### 6.1 User-Facing Analytics

- **Trending Events:** "Trending This Week" section on the homepage — ranked by view count + RSVP clicks over a rolling 7-day window
- **View counts:** Display view count on each event card or detail page (e.g., "👁 142 views")
- **Popular orgs:** Surface most-followed or most-viewed organizations

### 6.2 Admin Dashboard (Backend)

A private admin view (authenticated, admin-only) showing:

- **Scraper health:**
  - Last run time per source (PlanIt Purple, Instagram, Email, each department)
  - Success/failure status and error logs
  - Events ingested per source per run
  - Cookie expiry warnings (Instagram)
- **Content metrics:**
  - Total events in DB (active / past)
  - Events by source breakdown
  - Events by category breakdown
  - Duplicate detection rate
- **User metrics:**
  - Total registered users
  - DAU / WAU / MAU
  - Most popular categories and orgs
  - Recommendation engagement (click-through rate on recommended events)
- **Data tracking storage:** `event_views` table (event_id, user_id nullable, timestamp) and aggregate rollup tables for fast dashboard queries

---

## 7. Infrastructure & Automation (Priority #3)

### 7.1 Move Scraper Off Local Mac

The scraper currently runs on a personal Mac, which is a single point of failure (laptop closed, battery dead, network down, cookie expiry unnoticed). Plan:

- **Target:** Deploy scraper to a cloud server or container service
- **Options (evaluate in order):**
  1. **Render Background Worker** — keeps everything on Render alongside the DB and API
  2. **Railway** — simple container deployment with cron support
  3. **Cheap VPS (e.g., Hetzner, DigitalOcean)** — more control, can run Ollama remotely too
- **Ollama dependency:** Whichever host runs the scraper also needs access to an Ollama instance. Options:
  - Run Ollama on the same server (needs ≥16GB RAM for Gemma 3 12B)
  - Use a smaller model (`gemma3:4b`) on a cheaper server
  - Swap to an API-based LLM (Anthropic/OpenAI) — `ollama_url` config makes this a clean swap
- **SQLite elimination:** Once running in the cloud alongside Postgres, the SQLite → Postgres sync step can be removed. Scraper writes directly to Render Postgres.

### 7.2 Scheduled Runs

- **Cron schedule (proposed):**
  - PlanIt Purple: Every 6 hours
  - Instagram: Every 2 hours (cycles through 15 orgs per run, full rotation ≈ every 50 hours)
  - Email: Every 1 hour
  - Department websites: Every 12 hours
- **Implementation:** Cron jobs on the cloud host, or a task scheduler (APScheduler, Celery Beat) within the Python app

### 7.3 Monitoring & Alerts

- **Scraper failure alerts:** Notify on consecutive failures (email or Discord webhook)
- **Instagram cookie expiry:** Detect 401/403 responses and alert immediately
- **Stale data detection:** Alert if a source produces 0 new events for an unusual period
- **Logging:** Structured JSON logs, retained for at least 7 days

---

## 8. Frontend Enhancements (Priority #4)

### 8.1 New Pages / Components

- **Auth pages:** Sign up, log in, forgot password
- **Onboarding flow:** Category + org selection after first sign-up
- **Personalized feed:** Default homepage view for logged-in users with recommended events section
- **"My Events" page:** Saved/bookmarked events for logged-in users
- **Event detail page improvements:** View count display, save/bookmark button, RSVP click tracking
- **Trending section:** "Trending This Week" on homepage
- **Admin dashboard:** Protected route for admin users — scraper health, content metrics, user metrics

### 8.2 Existing UI Improvements

- **Search:** Full-text search across event titles and descriptions
- **Org pages:** Show upcoming events for a specific org
- **Free food filter:** Toggle to show only events with free food (data already captured)
- **Calendar view:** Optional calendar layout in addition to list view
- **Mobile responsiveness:** Audit and improve mobile experience

---

## 9. Database Schema Additions

### 9.1 New Tables

```sql
-- User accounts
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User explicit preferences
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50),  -- from category enum
    org_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- User activity tracking (implicit preferences)
CREATE TABLE user_activity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,  -- 'view', 'save', 'rsvp_click', 'unsave'
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Event view tracking (supports anonymous views too)
CREATE TABLE event_views (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),  -- nullable for anonymous
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Event embeddings for recommendations
CREATE TABLE event_embeddings (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE UNIQUE,
    embedding VECTOR(768),  -- dimension depends on Gemma model output
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scraper run logs (for admin dashboard)
CREATE TABLE scraper_runs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- 'planit_purple', 'instagram', 'email', 'dept_cs', etc.
    status VARCHAR(20) NOT NULL,  -- 'success', 'failure', 'partial'
    events_found INTEGER DEFAULT 0,
    events_new INTEGER DEFAULT 0,
    events_duplicate INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds FLOAT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP DEFAULT NOW()
);
```

### 9.2 Existing Table Modifications

- **events:** Add `view_count INTEGER DEFAULT 0` (denormalized for fast reads, updated periodically from `event_views`)
- **events:** Add `save_count INTEGER DEFAULT 0` (denormalized)

---

## 10. API Additions (FastAPI)

### 10.1 Auth Endpoints

| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| POST   | `/auth/signup`     | Create account           |
| POST   | `/auth/login`      | Login, returns JWT       |
| POST   | `/auth/logout`     | Invalidate token         |
| POST   | `/auth/forgot`     | Send password reset email|
| POST   | `/auth/reset`      | Reset password with token|

### 10.2 User Endpoints

| Method | Endpoint                    | Description                        |
|--------|-----------------------------|------------------------------------|
| GET    | `/me`                       | Get current user profile           |
| PUT    | `/me/preferences`           | Update category/org preferences    |
| GET    | `/me/saved`                 | Get saved events                   |
| POST   | `/events/{id}/save`         | Save/bookmark an event             |
| DELETE | `/events/{id}/save`         | Unsave an event                    |
| GET    | `/recommendations`          | Get personalized event recommendations |

### 10.3 Analytics Endpoints

| Method | Endpoint                    | Description                        |
|--------|-----------------------------|------------------------------------|
| POST   | `/events/{id}/view`         | Track an event view                |
| POST   | `/events/{id}/rsvp-click`   | Track an RSVP link click           |
| GET    | `/trending`                 | Get trending events (7-day window) |

### 10.4 Admin Endpoints (Admin-Only)

| Method | Endpoint                    | Description                        |
|--------|-----------------------------|------------------------------------|
| GET    | `/admin/scraper-health`     | Scraper run statuses and logs      |
| GET    | `/admin/metrics/content`    | Event counts by source/category    |
| GET    | `/admin/metrics/users`      | User engagement metrics            |
| GET    | `/admin/metrics/recommendations` | Recommendation click-through rates |

---

## 11. Tech Stack Summary

| Layer              | Technology                          |
|--------------------|-------------------------------------|
| Scraper            | Python (requests, BeautifulSoup, Gmail API) |
| LLM                | Ollama (Gemma 3 12B, local → cloud) |
| Database           | Postgres on Render (pgvector for embeddings) |
| Backend API        | FastAPI (Python)                    |
| Auth               | Email/password, JWT                 |
| Frontend           | Next.js on Vercel                   |
| Hosting (scraper)  | Local Mac → migrate to Render/Railway/VPS |

---

## 12. Implementation Roadmap

### Phase 1 — Personalization (Weeks 1-4)
1. User auth (signup/login/JWT) in FastAPI
2. User preferences table + onboarding API endpoints
3. Activity tracking (views, saves, RSVP clicks) — backend endpoints + frontend integration
4. Event embedding generation pipeline via Ollama
5. Recommendation engine (cosine similarity on embeddings)
6. Frontend: auth pages, onboarding flow, personalized feed, save buttons, "My Events" page

### Phase 2 — Analytics (Weeks 5-7)
1. Event view & RSVP click tracking (backend + frontend)
2. Trending events algorithm (rolling 7-day weighted score)
3. Frontend: trending section, view counts on event cards
4. Admin dashboard: scraper health, content metrics, user metrics
5. `scraper_runs` logging integrated into all existing scrapers

### Phase 3 — Automation & Reliability (Weeks 8-10)
1. Deploy scraper to cloud (Render worker or VPS)
2. Set up Ollama on cloud host (or swap to API-based LLM)
3. Eliminate SQLite → direct Postgres writes
4. Cron scheduling for all sources
5. Monitoring & alerting (failure detection, cookie expiry, stale data)

### Phase 4 — Frontend Polish (Weeks 11-12)
1. Full-text search
2. Free food filter toggle
3. Org detail pages with upcoming events
4. Calendar view option
5. Mobile responsiveness audit

### Phase 5 — New Sources (Weeks 13+)
1. Build first 5 department website scrapers
2. Evaluate coverage and add remaining 5-10 departments
3. Integrate into scraper rotation and admin dashboard

---

## 13. Open Questions

1. **Embedding dimensions:** What embedding size does Gemma 3 produce via Ollama? Need to confirm for `pgvector` column definition.
2. **Recommendation refresh:** Should recommendations recompute on every page load, on login, or via a daily batch job?
3. **Password reset:** What email service for transactional auth emails (SendGrid, Resend, AWS SES)?
4. **Instagram cookie refresh:** Any plan to automate cookie export, or will this remain a manual step?
5. **Rate limiting:** Should the FastAPI endpoints have rate limiting to prevent abuse?
6. **Privacy:** What data retention policy for user activity tracking? GDPR-style deletion on account delete?
7. **Admin access:** How many admin users? Just you, or a team?
8. **Department website list:** Finalize the remaining 5 departments beyond the initial list.
9. **Cloud LLM budget:** If moving off local Ollama to an API, what's the monthly budget ceiling?
10. **Notification system:** Any interest in push notifications or email digests for recommended events (future scope)?
