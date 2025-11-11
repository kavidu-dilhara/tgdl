"""Module for listing Telegram channels and groups."""

import asyncio
from typing import List, Dict
import click
from tgdl.auth import get_authenticated_client


async def get_channels() -> List[Dict[str, any]]:
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
    
    return channels


async def get_groups() -> List[Dict[str, any]]:
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
    
    return groups


def display_channels(channels: List[Dict[str, any]]):
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


def display_groups(groups: List[Dict[str, any]]):
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
