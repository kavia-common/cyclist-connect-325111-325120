import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


def _utcnow() -> datetime:
    """Return a timezone-aware UTC 'now'."""
    return datetime.now(timezone.utc)


metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("email", String(320), nullable=False, unique=True, index=True),
    Column("password_hash", String(255), nullable=False),
    Column("display_name", String(120), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_utcnow),
)

profiles = Table(
    "profiles",
    metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("display_name", String(120), nullable=True),
    Column("bio", Text, nullable=True),
    Column("pace", String(32), nullable=True),
    Column("bike_type", String(32), nullable=True),
    Column("looking_for", String(32), nullable=True),
    Column("home_base", String(120), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow),
)

locations = Table(
    "locations",
    metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("lat", Float, nullable=False),
    Column("lng", Float, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow),
)

conversations = Table(
    "conversations",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_utcnow),
)

conversation_participants = Table(
    "conversation_participants",
    metadata,
    Column("conversation_id", String(36), ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("conversation_id", "user_id", name="uq_conversation_participants"),
)

messages = Table(
    "messages",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("conversation_id", String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("sender_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("text", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_utcnow, index=True),
)

rides = Table(
    "rides",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("creator_id", String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
    Column("title", String(200), nullable=False),
    Column("date", String(10), nullable=True),  # ISO date 'YYYY-MM-DD' as frontend uses strings
    Column("time", String(5), nullable=True),  # 'HH:MM'
    Column("pace", String(32), nullable=True),
    Column("distance_km", Float, nullable=True),
    Column("start", String(200), nullable=True),
    Column("notes", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=_utcnow),
)


def get_engine() -> Engine:
    """Create (or reuse) the SQLAlchemy engine."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # NOTE: env var must be provided by orchestration; do not hardcode secrets here.
        raise RuntimeError("DATABASE_URL is not set")
    return create_engine(database_url, pool_pre_ping=True)


_SessionLocal = None


def get_sessionmaker() -> sessionmaker:
    """Return a module-level cached sessionmaker."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)
    return _SessionLocal


@contextmanager
def session_scope():
    """Context manager for a DB session with automatic commit/rollback."""
    SessionLocal = get_sessionmaker()
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def ensure_schema() -> None:
    """Create tables if they do not exist.

    Uses SQLAlchemy's metadata.create_all which is safe for initial bootstrap.
    """
    engine = get_engine()
    metadata.create_all(bind=engine)


def ping_db() -> None:
    """Lightweight DB ping used by health endpoint."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        conn.commit()
