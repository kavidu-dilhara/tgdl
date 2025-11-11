"""Main CLI interface for tgdl."""

import asyncio
import click
from tgdl import __version__
from tgdl.auth import login_user, check_auth
from tgdl.list import get_channels, get_groups, display_channels, display_groups
from tgdl.downloader import Downloader, MediaType
from tgdl.config import get_config


def run_async(coro):
    """Helper to run async functions."""
    return asyncio.run(coro)


@click.group()
@click.version_option(version=__version__, prog_name="tgdl")
def main():
    """
    tgdl - High-performance Telegram media downloader CLI tool.
    
    Download media from Telegram channels, groups, and message links with filters.
    
    \b
    Quick Start:
      1. Login:         tgdl login
      2. List channels: tgdl channels
      3. Download:      tgdl download -c CHANNEL_ID
    
    \b
    Examples:
      tgdl login
      tgdl channels
      tgdl download -c 1234567890 -p -v
      tgdl download -g 1234567890 --max-size 100MB
      tgdl download-link https://t.me/c/1234567890/123
    """
    pass


@main.command()
@click.option('--api-id', prompt='Telegram API ID', type=int, help='Your Telegram API ID')
@click.option('--api-hash', prompt='Telegram API Hash', help='Your Telegram API Hash')
@click.option('--phone', prompt='Phone number (with country code)', help='Phone number like +1234567890')
def login(api_id, api_hash, phone):
    """
    Login to Telegram and save session.
    
    Get API credentials from https://my.telegram.org/apps
    """
    click.echo(click.style("\n🔐 Telegram Login", fg='cyan', bold=True))
    click.echo("Get your API credentials from: https://my.telegram.org/apps\n")
    
    success = run_async(login_user(api_id, api_hash, phone))
    
    if success:
        click.echo(click.style("\n✓ Session saved successfully!", fg='green'))
        click.echo("You can now use other tgdl commands.")
    else:
        click.echo(click.style("\n✗ Login failed. Please try again.", fg='red'))


@main.command()
def channels():
    """List all channels you're a member of."""
    click.echo(click.style("📢 Fetching your channels...\n", fg='cyan'))
    
    channels_list = run_async(get_channels())
    display_channels(channels_list)
    
    if channels_list:
        click.echo(click.style(f"\n💡 Tip: Use 'tgdl download -c <ID>' to download from a channel", fg='yellow'))


@main.command()
def groups():
    """List all groups you're a member of."""
    click.echo(click.style("👥 Fetching your groups...\n", fg='cyan'))
    
    groups_list = run_async(get_groups())
    display_groups(groups_list)
    
    if groups_list:
        click.echo(click.style(f"\n💡 Tip: Use 'tgdl download -g <ID>' to download from a group", fg='yellow'))


@main.command()
@click.option('-c', '--channel', type=int, help='Channel ID to download from')
@click.option('-g', '--group', type=int, help='Group ID to download from')
@click.option('-p', '--photos', is_flag=True, help='Download only photos')
@click.option('-v', '--videos', is_flag=True, help='Download only videos')
@click.option('-a', '--audio', is_flag=True, help='Download only audio files')
@click.option('-d', '--documents', is_flag=True, help='Download only documents')
@click.option('--max-size', type=str, help='Maximum file size (e.g., 100MB, 1GB)')
@click.option('--min-size', type=str, help='Minimum file size (e.g., 1MB, 10KB)')
@click.option('--limit', type=int, help='Maximum number of files to download')
@click.option('--concurrent', type=int, default=5, help='Number of parallel downloads (default: 5)')
@click.option('-o', '--output', type=str, default='downloads', help='Output directory (default: downloads)')
def download(channel, group, photos, videos, audio, documents, max_size, min_size, limit, concurrent, output):
    """
    Download media from a channel or group with filters.
    
    \b
    Examples:
      # Download all media from a channel
      tgdl download -c 1234567890
      
      # Download only photos and videos
      tgdl download -c 1234567890 -p -v
      
      # Download with file size limit
      tgdl download -g 1234567890 --max-size 100MB
      
      # Download first 50 files
      tgdl download -c 1234567890 --limit 50
      
      # Fast download with 10 parallel connections
      tgdl download -c 1234567890 --concurrent 10
    """
    # Validate input
    if not channel and not group:
        click.echo(click.style("✗ Please specify either --channel or --group", fg='red'))
        click.echo("Use 'tgdl channels' or 'tgdl groups' to list available IDs")
        return
    
    if channel and group:
        click.echo(click.style("✗ Please specify only one: --channel OR --group", fg='red'))
        return
    
    entity_id = channel or group
    entity_type = "channel" if channel else "group"
    
    # Determine media types
    media_types = []
    if photos:
        media_types.append(MediaType.PHOTO)
    if videos:
        media_types.append(MediaType.VIDEO)
    if audio:
        media_types.append(MediaType.AUDIO)
    if documents:
        media_types.append(MediaType.DOCUMENT)
    
    # If no specific type selected, download all
    if not media_types:
        media_types.append(MediaType.ALL)
    
    # Parse file sizes
    max_size_bytes = _parse_size(max_size) if max_size else None
    min_size_bytes = _parse_size(min_size) if min_size else None
    
    # Display settings
    click.echo(click.style(f"\n📥 Download Settings", fg='cyan', bold=True))
    click.echo(f"  Entity: {entity_type.capitalize()} {entity_id}")
    click.echo(f"  Media types: {', '.join([mt.value for mt in media_types])}")
    if max_size:
        click.echo(f"  Max size: {max_size}")
    if min_size:
        click.echo(f"  Min size: {min_size}")
    if limit:
        click.echo(f"  Limit: {limit} files")
    click.echo(f"  Parallel downloads: {concurrent}")
    click.echo(f"  Output: {output}")
    click.echo()
    
    # Create downloader
    downloader = Downloader(
        max_concurrent=concurrent,
        media_types=media_types,
        max_size=max_size_bytes,
        min_size=min_size_bytes,
        output_dir=output,
    )
    
    # Start download
    count = run_async(downloader.download_from_entity(entity_id, limit))
    
    if count > 0:
        click.echo(click.style(f"\n🎉 Download complete! {count} files downloaded.", fg='green', bold=True))
    else:
        click.echo(click.style("\n⚠ No files downloaded.", fg='yellow'))


@main.command('download-link')
@click.argument('link')
@click.option('-p', '--photos', is_flag=True, help='Accept only photos')
@click.option('-v', '--videos', is_flag=True, help='Accept only videos')
@click.option('-a', '--audio', is_flag=True, help='Accept only audio files')
@click.option('-d', '--documents', is_flag=True, help='Accept only documents')
@click.option('--max-size', type=str, help='Maximum file size (e.g., 100MB, 1GB)')
@click.option('--min-size', type=str, help='Minimum file size (e.g., 1MB, 10KB)')
@click.option('-o', '--output', type=str, default='downloads', help='Output directory')
def download_link(link, photos, videos, audio, documents, max_size, min_size, output):
    """
    Download media from a single message link.
    
    \b
    Examples:
      tgdl download-link https://t.me/channel/123
      tgdl download-link https://t.me/c/1234567890/123
      tgdl download-link https://t.me/channel/123 -v --max-size 100MB
    """
    # Determine media types
    media_types = []
    if photos:
        media_types.append(MediaType.PHOTO)
    if videos:
        media_types.append(MediaType.VIDEO)
    if audio:
        media_types.append(MediaType.AUDIO)
    if documents:
        media_types.append(MediaType.DOCUMENT)
    
    # If no specific type selected, accept all
    if not media_types:
        media_types.append(MediaType.ALL)
    
    # Parse file sizes
    max_size_bytes = _parse_size(max_size) if max_size else None
    min_size_bytes = _parse_size(min_size) if min_size else None
    
    # Create downloader
    downloader = Downloader(
        max_concurrent=1,
        media_types=media_types,
        max_size=max_size_bytes,
        min_size=min_size_bytes,
        output_dir=output,
    )
    
    click.echo(click.style(f"\n📥 Downloading from link...\n", fg='cyan'))
    
    # Download
    success = run_async(downloader.download_from_link(link))
    
    if success:
        click.echo(click.style("\n✓ Download complete!", fg='green', bold=True))
    else:
        click.echo(click.style("\n✗ Download failed.", fg='red'))


@main.command()
def status():
    """Check authentication status and configuration."""
    config = get_config()
    
    click.echo(click.style("\n📊 tgdl Status\n", fg='cyan', bold=True))
    
    # Check authentication
    is_auth = run_async(check_auth())
    
    if is_auth:
        click.echo(click.style("✓ Authenticated", fg='green'))
    else:
        click.echo(click.style("✗ Not authenticated", fg='red'))
        click.echo("  Run 'tgdl login' to authenticate")
    
    # Show config location
    click.echo(f"\nConfig directory: {config.config_dir}")
    click.echo(f"Session file: {config.session_file}")
    click.echo(f"Progress file: {config.progress_file}")
    
    # Show API credentials (masked)
    api_id, api_hash = config.get_api_credentials()
    if api_id:
        click.echo(f"\nAPI ID: {api_id}")
        click.echo(f"API Hash: {'*' * 8}{api_hash[-4:] if api_hash else 'Not set'}")
    else:
        click.echo("\nAPI credentials: Not configured")


def _parse_size(size_str: str) -> int:
    """Parse size string like '100MB' to bytes."""
    size_str = size_str.upper().strip()
    
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
    }
    
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-len(unit)])
                return int(number * multiplier)
            except ValueError:
                pass
    
    # Try parsing as plain number (bytes)
    try:
        return int(size_str)
    except ValueError:
        click.echo(click.style(f"✗ Invalid size format: {size_str}", fg='red'))
        click.echo("Use formats like: 100MB, 1.5GB, 500KB")
        return 0


if __name__ == '__main__':
    main()
