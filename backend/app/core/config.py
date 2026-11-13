"""Service configuration loaded from environment variables.

The defaults are chosen so that the backend (and ``pytest``) runs fully
autonomously without any external PostgreSQL / Redis instance:

* ``DATABASE_URL`` defaults to a local SQLite file (PostgreSQL is used only
  when the variable is explicitly set, e.g. by ``docker-compose``);
* ``REDIS_URL`` defaults to the local Redis, and the cache layer transparently
  falls back to an in-memory store when Redis is unreachable.
"""

import os
import re
from typing import List
from dotenv import load_dotenv

from app.core.logging import logger

load_dotenv()


class Settings:
    """Application settings, read from the process environment."""

    def __init__(self) -> None:
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "sqlite:///./test.db",
        )
        self.REDIS_URL: str = os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0",
        )

        # CORS
        raw_cors = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:8501,http://localhost:3000,http://127.0.0.1:8501,http://127.0.0.1:3000,http://136.234.72.54,http://136.234.72.54:8000,http://25.vibe.fast.ru,http://25.vibe.fast.ru:8000",
        )
        self.CORS_ORIGINS: List[str] = [
            origin.strip() for origin in raw_cors.split(",") if origin.strip()
        ]

        # In production every origin must be served over HTTPS. Localhost is
        # allowed only for development tooling; everything else must be secure.
        if self.ENVIRONMENT == "production":
            localhost_prefixes = (
                "http://localhost",
                "https://localhost",
                "http://127.0.0.1",
                "https://127.0.0.1",
            )
            for origin in self.CORS_ORIGINS:
                if not origin.startswith("https://") and not origin.startswith(
                    localhost_prefixes
                ):
                    logger.warning(
                        "Non-HTTPS CORS origin '%s' configured in production", origin
                    )

        # LLM / GPTunnel
        self.GPTUNNEL_API_KEY: str = os.getenv("GPTUNNEL_API_KEY", "")
        self.GPTUNNEL_BASE_URL: str = os.getenv(
            "GPTUNNEL_BASE_URL",
            "https://gptunnel.ru/v1",
        )
        self.LLM_MODEL: str = os.getenv(
            "LLM_MODEL",
            "gptunnel/deepseek-v4-pro-tunnelcode",
        )

        # API authentication (MVP). Empty string disables the check.
        self.API_KEY: str = os.getenv("API_KEY", "")

        if self.ENVIRONMENT == "production":
            self._validate_production_database()

    def _validate_production_database(self) -> None:
        """Refuse to run production with an insecure database configuration.

        SQLite is not suitable for production, and default/weak passwords
        (``postgres``, ``password``, ``admin``, ...) must never be shipped in
        a real deployment. Failing fast here prevents a misconfigured release.
        """
        if self.DATABASE_URL.startswith("sqlite"):
            raise ValueError(
                "SQLite is not allowed in production; configure DATABASE_URL to a PostgreSQL instance"
            )
        if re.search(r":(postgres|password|admin|123456|changeme|qwerty)@", self.DATABASE_URL):
            logger.warning(
                "DATABASE_URL contains a default/weak password; replace it with a strong secret"
            )


settings = Settings()
