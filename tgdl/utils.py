"""Utility functions for tgdl."""

from functools import wraps
import click
from tgdl.auth import check_auth
import asyncio


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable size.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "10.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


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
        # Run async check_auth
        is_authenticated = asyncio.run(check_auth())
        
        if not is_authenticated:
            click.echo(click.style("\n✗ You're not logged in.", fg='red'))
            click.echo("Run 'tgdl login' first to authenticate.\n")
            return
        
        return func(*args, **kwargs)
    
    return wrapper
