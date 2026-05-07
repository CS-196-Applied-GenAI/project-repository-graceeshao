import os

import bcrypt

PRODUCTION = os.environ.get("PORCH_PRODUCTION") == "1"

# Cookie session secret. Override in prod via the PORCH_SECRET env var.
SESSION_SECRET = os.environ.get("PORCH_SECRET", "dev-secret-change-me")
if PRODUCTION and SESSION_SECRET == "dev-secret-change-me":
    raise RuntimeError(
        "PORCH_PRODUCTION=1 but PORCH_SECRET is unset — refusing to start. "
        "Set PORCH_SECRET to a random value before serving real traffic."
    )

SESSION_COOKIE = "porch_session"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def initials_from(display_name: str) -> str:
    parts = [p for p in display_name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:1].upper()
    return (parts[0][:1] + parts[-1][:1]).upper()
