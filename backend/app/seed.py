"""Seed the SQLite database with the demo data shown in frontend/Porch.html.

The mockup centers on a "today" of Thursday — for the seed we anchor "today"
to the real current date so the calendar and feed always return live-looking
data. Events are laid out across the surrounding Sun→Sat week.

Run with:  python -m app.seed
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import delete

from .database import Base, SessionLocal, engine
from .models import Event, FriendGroup, Friendship, Notification, PorchPresence, Rsvp, User
from .security import hash_password

DEMO_USER_EMAIL = "grace@porch.local"
DEMO_USER_PASSWORD = "porchporch"


# Group palette — values pulled from frontend/Porch.html.
GROUPS = [
    ("close",   "Close",     "#2F6B4A"),
    ("gym",     "Gym crew",  "#B8623A"),
    ("work",    "Work",      "#4A6E7A"),
    ("college", "College",   "#C18A2B"),
    ("self",    "You",       "#7A4E8C"),
]

# (email, display_name, initials, group_slug)
FRIENDS = [
    ("sam@porch.local",  "Sam Park",   "SP", "close"),
    ("lin@porch.local",  "Lin Chen",   "LC", "close"),
    ("mei@porch.local",  "Mei Tanaka", "MT", "close"),
    ("jake@porch.local", "Jake Reyes", "JR", "gym"),
    ("ari@porch.local",  "Ari Singh",  "AS", "college"),
    ("dev@porch.local",  "Devon Lee",  "DL", "work"),
]

# (dow_sun0, start_hour, duration_h, title, venue, group_slug, owner_email, tentative)
# Mirrors CAL_EVENTS + the "What's happening" feed in the mockup.
EVENTS = [
    (0,  9.5, 1.0, "Bagels w/ Sam",            "Big Jones",                "close",   "sam@porch.local",   False),
    (0, 14.0, 2.0, "Reading at Volumes",       "Volumes Bookcafe",         "self",    DEMO_USER_EMAIL,     False),
    (1,  8.0, 1.0, "Pilates",                  "Studio Three",             "gym",     "jake@porch.local",  False),
    (1, 17.5, 2.0, "Happy hour",               "Lone Wolf",                "work",    "dev@porch.local",   True),
    (2,  7.0, 1.0, "Lakefront run",            "Lakefront Trail",          "gym",     "jake@porch.local",  False),
    (2, 12.5, 1.0, "Lunch · Sweetgreen",  "Sweetgreen",               "work",    "dev@porch.local",   False),
    (2, 19.0, 2.5, "Trivia night",             "Owen & Engine",            "college", "ari@porch.local",   False),
    (3, 18.0, 2.0, "Pottery class",            "Lillstreet Art Center",    "close",   "lin@porch.local",   False),
    (4,  8.0, 1.0, "Pilates",                  "Studio Three",             "gym",     "jake@porch.local",  False),
    (4, 12.0, 1.0, "Coffee at Intelligentsia", "Intelligentsia, Logan Sq.", "self",   DEMO_USER_EMAIL,     False),
    (4, 17.5, 1.5, "Studio Three Pilates",     "Studio Three",             "self",    DEMO_USER_EMAIL,     True),
    (4, 20.0, 2.0, "Movie at Music Box",       "Music Box Theatre",        "college", "ari@porch.local",   False),
    (5, 18.0, 3.0, "Dinner at Avec",           "Avec, West Loop",          "close",   "lin@porch.local",   False),
    (5, 22.0, 2.0, "Late drinks at Marz",      "Marz Brewing",             "college", "ari@porch.local",   False),
    (6,  9.0, 2.0, "Farmers market",           "Logan Square Mkt",         "close",   "mei@porch.local",   False),
    (6, 16.0, 2.0, "Pickup soccer",            "Palmer Square Park",       "gym",     "jake@porch.local",  False),
]


def _start_of_week(today: date) -> date:
    """Sunday on or before `today` — matches the mockup's Sun-anchored week."""
    # Python: Monday=0..Sunday=6. We want Sunday=0, so shift.
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)


def _at(week_start: date, dow: int, hour_float: float) -> datetime:
    h = int(hour_float)
    m = round((hour_float - h) * 60)
    return datetime.combine(week_start + timedelta(days=dow), time(h, m))


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Wipe in FK-safe order so re-running the seed is idempotent.
        for tbl in (Notification, PorchPresence, Rsvp, Event, Friendship, FriendGroup, User):
            db.execute(delete(tbl))
        db.commit()

        grace = User(
            email=DEMO_USER_EMAIL,
            display_name="Grace",
            initials="G",
            password_hash=hash_password(DEMO_USER_PASSWORD),
        )
        db.add(grace)
        db.flush()

        # Grace's own friend groups (used to label her self-events and to
        # categorize friends she sees in /friends).
        grace_groups: dict[str, FriendGroup] = {}
        for slug, label, color in GROUPS:
            g = FriendGroup(owner_id=grace.id, slug=slug, label=label, color=color)
            db.add(g)
            grace_groups[slug] = g
        db.flush()

        # Friends. Each friend also keeps a single matching FriendGroup that
        # contains Grace — that's how their events become visible to her.
        users_by_email: dict[str, User] = {DEMO_USER_EMAIL: grace}
        for email, name, initials, slug in FRIENDS:
            u = User(email=email, display_name=name, initials=initials)
            db.add(u)
            db.flush()
            users_by_email[email] = u

            # The friend's own group (e.g., Jake's "gym crew") with Grace inside.
            friend_group = FriendGroup(
                owner_id=u.id,
                slug=slug,
                label=dict((s, l) for s, l, _ in GROUPS)[slug],
                color=dict((s, c) for s, _, c in GROUPS)[slug],
            )
            db.add(friend_group)
            db.flush()
            db.add(Friendship(owner_id=u.id, friend_id=grace.id, group_id=friend_group.id))

            # Grace classifies the friend in her own group of the same slug.
            db.add(
                Friendship(
                    owner_id=grace.id,
                    friend_id=u.id,
                    group_id=grace_groups[slug].id,
                )
            )
        db.commit()

        week_start = _start_of_week(date.today())

        for dow, hour, dur, title, venue, slug, owner_email, tentative in EVENTS:
            owner = users_by_email[owner_email]
            # Pick the group owned by the *owner* of the event.
            group = (
                db.query(FriendGroup)
                .filter(FriendGroup.owner_id == owner.id, FriendGroup.slug == slug)
                .first()
            )
            starts = _at(week_start, dow, hour)
            ends = starts + timedelta(hours=dur)
            db.add(
                Event(
                    owner_id=owner.id,
                    group_id=group.id if group else None,
                    title=title,
                    venue=venue,
                    starts_at=starts,
                    ends_at=ends,
                    tentative=tentative,
                )
            )

        db.commit()
        print(f"Seeded: 1 demo user, {len(FRIENDS)} friends, {len(EVENTS)} events.")
        print(f"Week anchored on Sunday {week_start.isoformat()}.")
        print(f"Demo login → email: {DEMO_USER_EMAIL}  password: {DEMO_USER_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
