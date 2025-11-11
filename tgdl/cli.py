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


def _format_size(bytes_size: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


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
      3. List groups:   tgdl groups
      4. Download:      tgdl download -c CHANNEL_ID
    
    \b
    Examples:
      tgdl login
      tgdl channels
      tgdl groups
      tgdl download -c 1234567890 -p -v
      tgdl download -g 1234567890 --max-size 100MB
      tgdl download-link https://t.me/c/1234567890/123
    """
    pass


@main.command()
def login():
    """
    Login to Telegram and save session.
    
    Get API credentials from https://my.telegram.org/apps
    """
    click.echo(click.style("\n🔐 Telegram Login", fg='cyan', bold=True))
    click.echo("Get your API credentials from: https://my.telegram.org/apps\n")
    
    # Check if already logged in
    is_auth = run_async(check_auth())
    if is_auth:
        try:
            from tgdl.auth import get_authenticated_client
            client = get_authenticated_client()
            if client:
                async def get_user_info():
                    await client.connect()
                    me = await client.get_me()
                    await client.disconnect()
                    return me
                me = run_async(get_user_info())
                click.echo(click.style(f"✓ You're already logged in as {me.first_name} (ID: {me.id})", fg='green'))
                click.echo("\nUse 'tgdl logout' to logout and login with a different account.")
                return
        except:
            pass
    
    try:
        api_id = click.prompt('Telegram API ID', type=int)
        api_hash = click.prompt('Telegram API Hash', type=str)
        phone = click.prompt('Phone number (with country code)', type=str)
        
        success = run_async(login_user(api_id, api_hash, phone))
        
        if success:
            click.echo(click.style("\n✓ Session saved successfully!", fg='green'))
            click.echo("You can now use other tgdl commands.")
        else:
            click.echo(click.style("\n✗ Login failed. Please try again.", fg='red'))
    except click.Abort:
        click.echo(click.style("\n\n⚠ Login cancelled by user.", fg='yellow'))
    except KeyboardInterrupt:
        click.echo(click.style("\n\n⚠ Login cancelled by user.", fg='yellow'))


@main.command()
def logout():
    """
    Logout from Telegram and remove session.
    
    This will delete your local session file and you'll need to login again.
    """
    import os
    from tgdl.config import get_config
    
    click.echo(click.style("\n🔓 Logout from Telegram\n", fg='cyan', bold=True))
    
    # Check if logged in
    is_auth = run_async(check_auth())
    if not is_auth:
        click.echo(click.style("✗ You're not logged in.", fg='yellow'))
        return
    
    # Confirm logout
    try:
        # Get user info before logout
        try:
            from tgdl.auth import get_authenticated_client
            client = get_authenticated_client()
            if client:
                async def get_user_info():
                    await client.connect()
                    me = await client.get_me()
                    await client.disconnect()
                    return me
                me = run_async(get_user_info())
                click.echo(f"Currently logged in as: {me.first_name} (ID: {me.id})\n")
        except:
            pass
        
        confirm = click.confirm("Are you sure you want to logout?", default=False)
        
        if not confirm:
            click.echo(click.style("\nLogout cancelled.", fg='yellow'))
            return
        
        # Delete session and config files
        config = get_config()
        session_file = config.session_file
        config_file = config.config_file
        progress_file = config.progress_file
        
        # Remove session file
        if os.path.exists(session_file):
            os.remove(session_file)
        
        # Remove session-journal file if exists
        if os.path.exists(session_file + '-journal'):
            os.remove(session_file + '-journal')
        
        # Remove config file
        if os.path.exists(config_file):
            os.remove(config_file)
        
        # Optionally remove progress file
        if os.path.exists(progress_file):
            click.echo(click.style("\n⚠️  Note: Downloaded files will NOT be deleted.", fg='yellow'))
            clear_progress = click.confirm("Do you want to clear download progress tracking? (Your files are safe)", default=False)
            if clear_progress:
                os.remove(progress_file)
                click.echo(click.style("  ✓ Progress tracking cleared (downloaded files still intact)", fg='green'))
        
        click.echo(click.style("\n✓ Successfully logged out!", fg='green'))
        click.echo("Run 'tgdl login' to login again.")
        click.echo(click.style("\n💡 Your downloaded files in 'downloads/' folder are safe.", fg='cyan'))
        
    except click.Abort:
        click.echo(click.style("\n\nLogout cancelled.", fg='yellow'))
    except KeyboardInterrupt:
        click.echo(click.style("\n\nLogout cancelled.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"\n✗ Error during logout: {e}", fg='red'))


@main.command()
def channels():
    """List all channels you're a member of."""
    # Check if logged in first
    if not run_async(check_auth()):
        click.echo(click.style("\n✗ You're not logged in.", fg='red'))
        click.echo("Run 'tgdl login' first to authenticate.\n")
        return
    
    click.echo(click.style("📢 Fetching your channels...\n", fg='cyan'))
    
    try:
        channels_list = run_async(get_channels())
        display_channels(channels_list)
        
        if channels_list:
            click.echo(click.style(f"\n💡 Tip: Use 'tgdl download -c <ID>' to download from a channel", fg='yellow'))
    except KeyboardInterrupt:
        click.echo(click.style("\n\n⚠ Cancelled by user.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg='red'))


@main.command()
def groups():
    """List all groups you're a member of."""
    # Check if logged in first
    if not run_async(check_auth()):
        click.echo(click.style("\n✗ You're not logged in.", fg='red'))
        click.echo("Run 'tgdl login' first to authenticate.\n")
        return
    
    click.echo(click.style("👥 Fetching your groups...\n", fg='cyan'))
    
    try:
        groups_list = run_async(get_groups())
        display_groups(groups_list)
        
        if groups_list:
            click.echo(click.style(f"\n💡 Tip: Use 'tgdl download -g <ID>' to download from a group", fg='yellow'))
    except KeyboardInterrupt:
        click.echo(click.style("\n\n⚠ Cancelled by user.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg='red'))


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
    if max_size_bytes:
        click.echo(f"  Max size: {max_size} ({_format_size(max_size_bytes)})")
    if min_size_bytes:
        click.echo(f"  Min size: {min_size} ({_format_size(min_size_bytes)})")
    if limit:
        click.echo(f"  Limit: {limit} files")
    click.echo(f"  Parallel downloads: {concurrent}")
    click.echo(f"  Output: {output}")
    click.echo(click.style("\n💡 Tip: Files already downloaded will be skipped automatically", fg='yellow'))
    click.echo(click.style("⚠️  Press Ctrl+C to cancel at any time\n", fg='yellow'))
    
    # Confirmation for large operations
    if not limit or limit > 100:
        try:
            if not click.confirm("Continue with download?", default=True):
                click.echo(click.style("\n⚠ Download cancelled.", fg='yellow'))
                return
        except (click.Abort, KeyboardInterrupt):
            click.echo(click.style("\n\n⚠ Download cancelled.", fg='yellow'))
            return
    
    # Create downloader
    downloader = Downloader(
        max_concurrent=concurrent,
        media_types=media_types,
        max_size=max_size_bytes,
        min_size=min_size_bytes,
        output_dir=output,
    )
    
    # Start download with error handling
    try:
        count = run_async(downloader.download_from_entity(entity_id, limit))
        
        if count > 0:
            click.echo(click.style(f"\n🎉 Download complete! {count} files downloaded.", fg='green', bold=True))
        else:
            click.echo(click.style("\n⚠ No files downloaded.", fg='yellow'))
    except KeyboardInterrupt:
        click.echo(click.style("\n\n⚠ Download cancelled by user.", fg='yellow'))
        click.echo(click.style("💡 You can resume by running the same command again.", fg='cyan'))
    except Exception as e:
        click.echo(click.style(f"\n✗ Error during download: {e}", fg='red'))


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
    
    click.echo(click.style(f"\n📥 Downloading from link", fg='cyan', bold=True))
    click.echo(f"Link: {link}")
    if max_size_bytes or min_size_bytes:
        if max_size_bytes:
            click.echo(f"Max size: {_format_size(max_size_bytes)}")
        if min_size_bytes:
            click.echo(f"Min size: {_format_size(min_size_bytes)}")
    click.echo()
    
    # Download with error handling
    try:
        success = run_async(downloader.download_from_link(link))
        
        if success:
            click.echo(click.style("\n✓ Download complete!", fg='green', bold=True))
        else:
            click.echo(click.style("\n✗ Download failed.", fg='red'))
    except KeyboardInterrupt:
        click.echo(click.style("\n\n⚠ Download cancelled by user.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg='red'))


@main.command()
def status():
    """Check authentication status and configuration."""
    config = get_config()
    
    click.echo(click.style("\n📊 tgdl Status\n", fg='cyan', bold=True))
    
    # Check authentication
    is_auth = run_async(check_auth())
    
    if is_auth:
        click.echo(click.style("✓ Authenticated", fg='green'))
        # Show user info
        try:
            from tgdl.auth import get_authenticated_client
            client = get_authenticated_client()
            if client:
                async def get_user_info():
                    await client.connect()
                    me = await client.get_me()
                    await client.disconnect()
                    return me
                me = run_async(get_user_info())
                click.echo(f"  Name: {me.first_name}" + (f" {me.last_name}" if me.last_name else ""))
                click.echo(f"  User ID: {me.id}")
                if me.username:
                    click.echo(f"  Username: @{me.username}")
        except Exception as e:
            pass
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
