"""Shared slowapi rate limiter for the API surface.

Kept in its own module so both ``app.main`` and the route modules can import
the same limiter instance without creating an import cycle.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
