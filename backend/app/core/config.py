"""Service configuration loaded from environment variables.

The defaults are chosen so that the backend (and ``pytest``) runs fully
autonomously without any external PostgreSQL / Redis instance:

* ``DATABASE_URL`` defaults to a local SQLite file (PostgreSQL is used only
  when the variable is explicitly set, e.g. by ``docker-compose``);
* ``REDIS_URL`` defaults to the local Redis, and the cache layer transparently
  falls back to an in-memory store when Redis is unreachable.
"""

import os


class Settings:
    """Application settings, read from the process environment."""

    def __init__(self) -> None:
        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "sqlite:///./test.db",
        )
        self.REDIS_URL: str = os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0",
        )


settings = Settings()
