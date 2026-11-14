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


def _migrate_columns() -> None:
    """Ensure newly added columns exist in older database tables without Alembic."""
    from sqlalchemy import inspect, text
    from app.core.logging import logger

    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            if "users" in inspector.get_table_names():
                existing_cols = {col["name"] for col in inspector.get_columns("users")}
                for col_name in ("first_name", "last_name", "phone", "personal_account", "address"):
                    if col_name not in existing_cols:
                        logger.info("Migrating database: adding missing column users.%s", col_name)
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} VARCHAR"))
                        conn.commit()
            if "bills" in inspector.get_table_names():
                bill_cols = {col["name"] for col in inspector.get_columns("bills")}
                for col_name in ("provider_name", "personal_account"):
                    if col_name not in bill_cols:
                        logger.info("Migrating database: adding missing column bills.%s", col_name)
                        conn.execute(text(f"ALTER TABLE bills ADD COLUMN {col_name} VARCHAR"))
                        conn.commit()
            if "bill_services" in inspector.get_table_names():
                svc_cols = {col["name"] for col in inspector.get_columns("bill_services")}
                for col_name in ("recalculation", "penalty"):
                    if col_name not in svc_cols:
                        logger.info("Migrating database: adding missing column bill_services.%s", col_name)
                        conn.execute(text(f"ALTER TABLE bill_services ADD COLUMN {col_name} NUMERIC(10, 2) DEFAULT 0.00"))
                        conn.commit()
    except Exception as exc:
        from app.core.logging import logger
        logger.warning("Auto-migration note: %s", exc)


def init_db() -> None:
    """Create all tables if they do not exist yet and seed the default demo user."""
    from app.db import crud, models  # noqa: F401  (register models on Base.metadata)

    Base.metadata.create_all(bind=engine)
    _migrate_columns()

    session = SessionLocal()
    try:
        demo = crud.get_user_by_email(session, "demo@utilitylens.ru")
        if demo is None:
            crud.create_user(
                session,
                username="demo",
                email="demo@utilitylens.ru",
                password="demo123",
                user_id="user_demo_01",
                first_name="Иван",
                last_name="Иванов",
                phone="+7 (900) 123-45-67",
                personal_account="40702810100000001234",
                address="г. Владивосток, ул. Светланская, д. 45, кв. 12",
            )
        elif not getattr(demo, "first_name", None):
            crud.update_user_profile(
                session,
                demo,
                first_name="Иван",
                last_name="Иванов",
                phone="+7 (900) 123-45-67",
                personal_account="40702810100000001234",
                address="г. Владивосток, ул. Светланская, д. 45, кв. 12",
            )
    except Exception:
        session.rollback()
    finally:
        session.close()

