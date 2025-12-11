"""Module for listing Telegram channels and groups."""

import asyncio
from typing import List, Dict, Any
import click
from telethon.tl.types import User
from tgdl.auth import get_authenticated_client


async def get_channels() -> List[Dict[str, Any]]:
    """
    Get list of all channels user is member of.
    
    Returns:
        List of dicts with channel info
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
        
        await client.disconnect()
        
    except Exception as e:
        click.echo(click.style(f"✗ Error fetching channels: {e}", fg='red'))
        try:
            await client.disconnect()
        except Exception:
            pass
    
    return channels


async def get_groups() -> List[Dict[str, Any]]:
    """
    Get list of all groups user is member of.
    
    Returns:
        List of dicts with group info
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
        
        await client.disconnect()
        
    except Exception as e:
        click.echo(click.style(f"✗ Error fetching groups: {e}", fg='red'))
        try:
            await client.disconnect()
        except Exception:
            pass
    
    return groups


async def get_bots() -> List[Dict[str, Any]]:
    """
    Get list of all bot chats user has.
    
    Returns:
        List of dicts with bot info
    """
    client = get_authenticated_client()
    if not client:
        return []
    
    bots = []
    try:
        await client.connect()
        
        dialogs = await client.get_dialogs()
        
        for dialog in dialogs:
            # Check if it's a user and a bot
            if dialog.is_user and isinstance(dialog.entity, User) and dialog.entity.bot:
                bots.append({
                    'id': dialog.entity.id,
                    'title': dialog.name,
                    'username': getattr(dialog.entity, 'username', None),
                })
        
        await client.disconnect()
        
    except Exception as e:
        click.echo(click.style(f"✗ Error fetching bots: {e}", fg='red'))
        try:
            await client.disconnect()
        except Exception:
            pass
    
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
        click.echo(f"{channel['id']:<15} {channel['title']:<40} {username:<20}")


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
        click.echo(f"{group['id']:<15} {group['title']:<40} {username:<20}")


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
        click.echo(f"{bot['id']:<15} {bot['title']:<40} {username:<20}")
