"""Utility functions for tgdl."""

from functools import wraps
import asyncio
import click
from tgdl.auth import check_auth


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable size.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted string (e.g., "10.5 MB")
    """
    # Use a local variable so the caller's value is never mutated (Bug #11)
    size = float(bytes_size)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def require_auth(func):
    """
    Decorator to require authentication for CLI commands.

    Fix #20: asyncio.run() raises RuntimeError if a loop is already running
    (e.g. inside pytest-asyncio or a Jupyter notebook). We detect that case
    and fall back to scheduling the coroutine on the existing loop instead.

    Usage:
        @main.command()
        @require_auth
        def my_command():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already inside a running loop — schedule and wait
                import concurrent.futures
                future = asyncio.run_coroutine_threadsafe(check_auth(), loop)
                is_authenticated = future.result(timeout=30)
            else:
                is_authenticated = loop.run_until_complete(check_auth())
        except RuntimeError:
            # No current event loop at all — create one via asyncio.run
            is_authenticated = asyncio.run(check_auth())

        if not is_authenticated:
            click.echo(click.style("\n✗ You're not logged in.", fg='red'))
            click.echo("Run 'tgdl login' first to authenticate.\n")
            return

        return func(*args, **kwargs)

    return wrapper
