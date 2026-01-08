"""
OpenTransit Common Utilities

Shared code used across all OpenTransit modules.
"""

__version__ = "0.1.0"

import os
from typing import Optional


def get_database_url() -> str:
    """Get database URL from environment."""
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://opentransit:opentransit@localhost:5432/opentransit'
    )


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    return os.environ.get(key, default)
