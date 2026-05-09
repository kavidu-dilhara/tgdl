"""Module for listing Telegram channels, groups, and bot chats."""

import logging
from typing import List, Dict, Any
import click
from telethon.tl.types import User
from tgdl.auth import get_authenticated_client

logger = logging.getLogger(__name__)

# Max display width for title column before truncating
_TITLE_MAX = 40


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len, appending '..' if cut.

    Fix #16 (display): long titles no longer overflow their column and
    break table alignment.
    """
    if len(text) <= max_len:
        return text
    return text[:max_len - 2] + '..'


async def get_channels() -> List[Dict[str, Any]]:
    """
    Get list of all channels user is member of.

    Fix #7: use try/finally so client.disconnect() is always called even when
    an unhandled exception escapes the except block.
    """
    client = get_authenticated_client()
    if not client:
        return []

    channels = []
    try:
        await client.connect()
        dialogs = await client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_channel:
                channels.append({
                    'id': dialog.entity.id,
                    'title': dialog.name,
                    'username': getattr(dialog.entity, 'username', None),
                })
    except Exception as e:
        click.echo(click.style(f"✗ Error fetching channels: {e}", fg='red'))
        logger.exception("Error fetching channels list")
    finally:
        try:
            await client.disconnect()
        except Exception as disc_err:
            logger.debug(f"Error disconnecting client: {disc_err}")

    return channels


async def get_groups() -> List[Dict[str, Any]]:
    """
    Get list of all groups user is member of.

    Fix #8: try/finally for guaranteed disconnect.
    """
    client = get_authenticated_client()
    if not client:
        return []

    groups = []
    try:
        await client.connect()
        dialogs = await client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_group:
                groups.append({
                    'id': dialog.entity.id,
                    'title': dialog.name,
                    'username': getattr(dialog.entity, 'username', None),
                })
    except Exception as e:
        click.echo(click.style(f"✗ Error fetching groups: {e}", fg='red'))
        logger.exception("Error fetching groups list")
    finally:
        try:
            await client.disconnect()
        except Exception as disc_err:
            logger.debug(f"Error disconnecting client: {disc_err}")

    return groups


async def get_bots() -> List[Dict[str, Any]]:
    """
    Get list of all bot chats user has.

    Fix #9: try/finally for guaranteed disconnect.
    """
    client = get_authenticated_client()
    if not client:
        return []

    bots = []
    try:
        await client.connect()
        dialogs = await client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_user and isinstance(dialog.entity, User) and dialog.entity.bot:
                bots.append({
                    'id': dialog.entity.id,
                    'title': dialog.name,
                    'username': getattr(dialog.entity, 'username', None),
                })
    except Exception as e:
        click.echo(click.style(f"✗ Error fetching bots: {e}", fg='red'))
        logger.exception("Error fetching bots list")
    finally:
        try:
            await client.disconnect()
        except Exception as disc_err:
            logger.debug(f"Error disconnecting client: {disc_err}")

    return bots


def display_channels(channels: List[Dict[str, Any]]) -> None:
    """Display channels in a formatted table."""
    if not channels:
        click.echo("No channels found.")
        return

    click.echo(click.style(f"\n📢 Found {len(channels)} channels:\n", fg='cyan', bold=True))
    click.echo(f"{'ID':<15} {'Title':<40} {'Username':<20}")
    click.echo("=" * 75)

    for channel in channels:
        username = f"@{channel['username']}" if channel['username'] else "N/A"
        title = _truncate(channel['title'], _TITLE_MAX)
        click.echo(f"{channel['id']:<15} {title:<40} {username:<20}")


def display_groups(groups: List[Dict[str, Any]]) -> None:
    """Display groups in a formatted table."""
    if not groups:
        click.echo("No groups found.")
        return

    click.echo(click.style(f"\n👥 Found {len(groups)} groups:\n", fg='cyan', bold=True))
    click.echo(f"{'ID':<15} {'Title':<40} {'Username':<20}")
    click.echo("=" * 75)

    for group in groups:
        username = f"@{group['username']}" if group['username'] else "N/A"
        title = _truncate(group['title'], _TITLE_MAX)
        click.echo(f"{group['id']:<15} {title:<40} {username:<20}")


def display_bots(bots: List[Dict[str, Any]]) -> None:
    """Display bot chats in a formatted table."""
    if not bots:
        click.echo("No bot chats found.")
        return

    click.echo(click.style(f"\n🤖 Found {len(bots)} bot chats:\n", fg='cyan', bold=True))
    click.echo(f"{'ID':<15} {'Bot Name':<40} {'Username':<20}")
    click.echo("=" * 75)

    for bot in bots:
        username = f"@{bot['username']}" if bot['username'] else "N/A"
        title = _truncate(bot['title'], _TITLE_MAX)
        click.echo(f"{bot['id']:<15} {title:<40} {username:<20}")
