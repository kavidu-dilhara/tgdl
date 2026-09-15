"""Utility functions for tgdl."""

import asyncio
import logging
from functools import wraps

import click

from tgdl.auth import check_auth

logger = logging.getLogger(__name__)


def format_bytes(bytes_size: int) -> str:
    if bytes_size is None:
        return "0.00 B"
    size = abs(float(bytes_size))
    prefix = "-" if bytes_size < 0 else ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0:
            return f"{prefix}{size:.2f} {unit}"
        size /= 1024.0
    return f"{prefix}{size:.2f} PB"


def require_auth(func):
    """Require authentication for synchronous Click commands."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            is_authenticated = asyncio.run(check_auth())
        else:
            raise click.ClickException(
                "This synchronous command cannot run inside an active asyncio event loop."
            )
        if not is_authenticated:
            raise click.ClickException("You're not logged in. Run 'tgdl login' first.")
        return func(*args, **kwargs)
    return wrapper
