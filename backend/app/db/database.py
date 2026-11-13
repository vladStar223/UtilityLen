"""Database engine, session factory and dependency for FastAPI.

The engine is created lazily (SQLAlchemy does not connect until the first
operation), so importing this module never requires a live database. SQLite
is the default backend for tests; PostgreSQL is used when ``DATABASE_URL``
points at it (see ``app.core.config``).
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models (see ``app.db.models``)."""


_db_url = settings.DATABASE_URL
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

_connect_args = (
    {"check_same_thread": False}
    if _db_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    _db_url,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they do not exist yet (dev/test convenience)."""
    from app.db import models  # noqa: F401  (register models on Base.metadata)

    Base.metadata.create_all(bind=engine)
