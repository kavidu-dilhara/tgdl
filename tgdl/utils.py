"""Utility functions for tgdl."""

from functools import wraps
import asyncio
import click
import logging
from tgdl.auth import check_auth

logger = logging.getLogger(__name__)


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable size.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted string (e.g., "10.5 MB")
    """
    if bytes_size is None:
        return "0.00 B"
    size = abs(float(bytes_size))
    prefix = "-" if bytes_size < 0 else ""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{prefix}{size:.2f} {unit}"
        size /= 1024.0
    return f"{prefix}{size:.2f} PB"


def require_auth(func):
    """
    Decorator to require authentication for CLI commands.

    Usage:
        @main.command()
        @require_auth
        def my_command():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            is_authenticated = asyncio.run(check_auth())
        except RuntimeError:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("No running event loop available for authentication check.")
                is_authenticated = False
            else:
                import concurrent.futures
                future = asyncio.run_coroutine_threadsafe(check_auth(), loop)
                is_authenticated = future.result(timeout=30)

        if not is_authenticated:
            click.echo(click.style("\n✗ You're not logged in.", fg='red'))
            click.echo("Run 'tgdl login' first to authenticate.\n")
            return

        return func(*args, **kwargs)

    return wrapper
