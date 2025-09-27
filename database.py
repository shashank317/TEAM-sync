"""database.py – central DB session/engine management

Enhancements:
 - Supports .env DATABASE_URL override
 - Adds SSL requirement automatically for Render Postgres unless disabled
 - Provides optional SQLite fallback for local development (USE_SQLITE=1)
 - Adds pool_pre_ping to mitigate stale connections / closed SSL tunnels
 - Removes hard‑coded secrets from source (encourage env usage)
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import quote_plus, urlparse, parse_qsl, urlencode, urlunparse
from dotenv import load_dotenv

load_dotenv()

# -------------------------------
# Helper: build URL if explicit DATABASE_URL not provided
# -------------------------------
def _build_postgres_url():
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "")
    if not (user and password and host and name):
        return None
    return f"postgresql+psycopg2://{user}:{quote_plus(password)}@{host}:{port}/{name}"


RAW_DATABASE_URL = os.getenv("DATABASE_URL") or _build_postgres_url()

# Optional: local SQLite override
USE_SQLITE = os.getenv("USE_SQLITE", "0") == "1"

def _normalize_url(url: str) -> str:
    """Normalize a Postgres DSN for SQLAlchemy usage.

    - Add +psycopg2 driver spec if missing.
    - Ensure sslmode=require for known managed hosts (neon.tech, render.com) if not present.
    - Preserve existing query parameters.
    """
    if not url:
        return url
    try:
        # Ensure driver segment
        if url.startswith("postgresql://") and "+psycopg2" not in url.split("//",1)[1]:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        parsed = urlparse(url)
        host = parsed.hostname or ""
        # Only append sslmode if host suggests managed provider and not already set
        if any(suffix in host for suffix in ("neon.tech", "render.com")):
            q = dict(parse_qsl(parsed.query, keep_blank_values=True))
            if "sslmode" not in q:
                q["sslmode"] = "require"
                parsed = parsed._replace(query=urlencode(q))
                url = urlunparse(parsed)
        return url
    except Exception:
        return url  # fail safe – never block startup

if USE_SQLITE:
    DB_KIND = "sqlite"
    DATABASE_URL = os.getenv("SQLITE_PATH", "sqlite:///./teamsync.db")
else:
    DB_KIND = "postgres"
    if not RAW_DATABASE_URL:
        DATABASE_URL = "sqlite:///./teamsync.db"
        DB_KIND = "sqlite"
    else:
        DATABASE_URL = _normalize_url(RAW_DATABASE_URL)

# Determine if we must enforce SSL (Render usually requires sslmode=require)
CONNECT_ARGS = {}
if DB_KIND == "postgres":
    ssl_mode = os.getenv("DB_SSLMODE")
    # If user explicitly sets DB_SSLMODE it overrides normalization.
    if ssl_mode:
        CONNECT_ARGS["sslmode"] = ssl_mode

# Engine creation with resilience
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "0") == "1",
    pool_pre_ping=True,
    connect_args=CONNECT_ARGS if CONNECT_ARGS else {},
    pool_recycle=1800,  # recycle every 30m to avoid dropped idle SSL conns
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility: quick runtime summary (only printed once when imported in dev)
if os.getenv("PRINT_DB_INFO", "0") == "1":
    print(f"[DB] Using {DB_KIND} database -> {DATABASE_URL}")
