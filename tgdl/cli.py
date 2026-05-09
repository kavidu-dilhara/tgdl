"""Main CLI interface for tgdl."""

import asyncio
import logging
import os
import click
from tgdl import __version__
from tgdl.auth import login_user
from tgdl.list import get_channels, get_groups, get_bots, display_channels, display_groups, display_bots
from tgdl.downloader import Downloader, MediaType, DEFAULT_MAX_CONCURRENT, MAX_CONCURRENT_LIMIT, DEFAULT_OUTPUT_DIR
from tgdl.config import get_config
from tgdl.utils import format_bytes, require_auth


def run_async(coro):
    """Helper to run async functions."""
    return asyncio.run(coro)


def _setup_logging():
    """Configure logging for the application."""
    log_level = os.environ.get('TGDL_LOG_LEVEL', 'WARNING').upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.WARNING),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.group()
@click.version_option(version=__version__, prog_name="tgdl")
def main():
    """
    tgdl - High-performance Telegram media downloader CLI tool.

    Download media from Telegram channels, groups, bot chats, and message links with filters.

    \b
    Quick Start:
      1. Login:         tgdl login
      2. List channels: tgdl channels
      3. List groups:   tgdl groups
      4. List bots:     tgdl bots
      5. Download:      tgdl download -c CHANNEL_ID / -g GROUP_ID / -b BOT_ID

    \b
    Examples:
      tgdl login
      tgdl channels
      tgdl groups
      tgdl bots
      tgdl download -c 1234567890 -p -v
      tgdl download -g 1234567890 --max-size 100MB
      tgdl download -b 1234567890 -d
      tgdl download-link https://t.me/c/1234567890/123

    \b
    Environment Variables:
      TGDL_LOG_LEVEL    Set logging level (DEBUG, INFO, WARNING, ERROR)
    """
    _setup_logging()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_user_info_with_client(client):
    """Fetch the logged-in user using an already-connected client."""
    try:
        me = await client.get_me()
        return me
    except Exception:
        return None


async def _check_auth_and_get_user():
    """Check auth and get user info in a single connection."""
    from tgdl.auth import get_authenticated_client
    client = get_authenticated_client()
    if not client:
        return False, None
    try:
        await client.connect()
        is_auth = await client.is_user_authorized()
        if not is_auth:
            return False, None
        me = await _get_user_info_with_client(client)
        return True, me
    except Exception:
        return False, None
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


def _parse_size(size_str: str):
    """Parse size string like '100MB' to bytes.

    Fix #1: units are now checked longest-first (TB → GB → MB → KB → B) so
    '100KB'.endswith('B') no longer matches the bare 'B' entry first and
    silently parses 100 KB as 100 bytes.

    Returns None on invalid input so callers can detect and abort rather than
    silently disabling the filter.
    """
    size_str = size_str.upper().strip()

    # Fix #1: ordered longest-suffix-first to avoid 'B' swallowing 'KB' etc.
    units = [
        ('TB', 1024 ** 4),
        ('GB', 1024 ** 3),
        ('MB', 1024 ** 2),
        ('KB', 1024),
        ('B',  1),
    ]

    for unit, multiplier in units:
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-len(unit)])
                if number < 0:
                    click.echo(click.style(f"\u2717 Size cannot be negative: {size_str}", fg='red'))
                    return None
                return int(number * multiplier)
            except ValueError:
                pass

    # Try plain integer (bytes)
    try:
        value = int(size_str)
        if value < 0:
            click.echo(click.style(f"\u2717 Size cannot be negative: {size_str}", fg='red'))
            return None
        return value
    except ValueError:
        click.echo(click.style(f"\u2717 Invalid size format: {size_str}", fg='red'))
        click.echo("Use formats like: 100MB, 1.5GB, 500KB")
        return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@main.command()
def login():
    """
    Login to Telegram and save session.

    Get API credentials from https://my.telegram.org/apps
    """
    click.echo(click.style("\n🔐 Telegram Login", fg='cyan', bold=True))
    click.echo("Get your API credentials from: https://my.telegram.org/apps\n")

    is_auth, existing_user = run_async(_check_auth_and_get_user())
    if existing_user:
        click.echo(click.style(
            f"✓ You're already logged in as {existing_user.first_name} (ID: {existing_user.id})",
            fg='green'
        ))
        click.echo("\nUse 'tgdl logout' to logout and login with a different account.")
        return

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
    click.echo(click.style("\n🔓 Logout from Telegram\n", fg='cyan', bold=True))

    is_auth, me = run_async(_check_auth_and_get_user())

    if me is None:
        click.echo(click.style("✗ You're not logged in.", fg='yellow'))
        return

    try:
        click.echo(f"Currently logged in as: {me.first_name} (ID: {me.id})\n")

        confirm = click.confirm("Are you sure you want to logout?", default=False)
        if not confirm:
            click.echo(click.style("\nLogout cancelled.", fg='yellow'))
            return

        config = get_config()
        session_file = config.session_file
        config_file = config.config_file
        progress_file = config.progress_file

        if os.path.exists(session_file):
            os.remove(session_file)

        session_journal = str(session_file) + '-journal'
        if os.path.exists(session_journal):
            os.remove(session_journal)

        if os.path.exists(config_file):
            os.remove(config_file)

        if os.path.exists(progress_file):
            click.echo(click.style("\n⚠️  Note: Downloaded files will NOT be deleted.", fg='yellow'))
            clear_progress = click.confirm(
                "Do you want to clear download progress tracking? (Your files are safe)",
                default=False
            )
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
@require_auth
def channels():
    """List all channels you're a member of."""
    click.echo(click.style("📢 Fetching your channels...\n", fg='cyan'))
    try:
        channels_list = run_async(get_channels())
        display_channels(channels_list)
        if channels_list:
            click.echo(click.style("\n💡 Tip: Use 'tgdl download -c <ID>' to download from a channel", fg='yellow'))
    except KeyboardInterrupt:
        click.echo(click.style("\n\n⚠ Cancelled by user.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg='red'))


@main.command()
@require_auth
def groups():
    """List all groups you're a member of."""
    click.echo(click.style("👥 Fetching your groups...\n", fg='cyan'))
    try:
        groups_list = run_async(get_groups())
        display_groups(groups_list)
        if groups_list:
            click.echo(click.style("\n💡 Tip: Use 'tgdl download -g <ID>' to download from a group", fg='yellow'))
    except KeyboardInterrupt:
        click.echo(click.style("\n\n⚠ Cancelled by user.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg='red'))


@main.command()
@require_auth
def bots():
    """List all bot chats you have."""
    click.echo(click.style("🤖 Fetching your bot chats...\n", fg='cyan'))
    try:
        bots_list = run_async(get_bots())
        display_bots(bots_list)
        if bots_list:
            click.echo(click.style("\n💡 Tip: Use 'tgdl download -b <ID>' to download from a bot chat", fg='yellow'))
    except KeyboardInterrupt:
        click.echo(click.style("\n\n⚠ Cancelled by user.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg='red'))


@main.command()
@require_auth  # Fix #3: download command was missing @require_auth
@click.option('-c', '--channel', type=int, help='Channel ID to download from')
@click.option('-g', '--group', type=int, help='Group ID to download from')
@click.option('-b', '--bot', type=int, help='Bot chat ID to download from')
@click.option('-p', '--photos', is_flag=True, help='Download only photos')
@click.option('-v', '--videos', is_flag=True, help='Download only videos')
@click.option('-a', '--audio', is_flag=True, help='Download only audio files')
@click.option('-d', '--documents', is_flag=True, help='Download only documents')
@click.option('--max-size', type=str, help='Maximum file size (e.g., 100MB, 1GB)')
@click.option('--min-size', type=str, help='Minimum file size (e.g., 1MB, 10KB)')
@click.option('--limit', type=int, help='Maximum number of files to download')
@click.option('--min-id', type=int, help='Start from this message ID (inclusive)')
@click.option('--max-id', type=int, help='Stop at this message ID (inclusive)')
@click.option('--concurrent', type=int, default=DEFAULT_MAX_CONCURRENT,
              help=f'Number of parallel downloads (default: {DEFAULT_MAX_CONCURRENT})')
@click.option('-o', '--output', type=str, default=DEFAULT_OUTPUT_DIR,
              help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})')
def download(channel, group, bot, photos, videos, audio, documents,
             max_size, min_size, limit, min_id, max_id, concurrent, output):
    """
    Download media from a channel, group, or bot chat with filters.

    \b
    Examples:
      tgdl download -c 1234567890
      tgdl download -g 1234567890 -p -v
      tgdl download -b 1234567890 -d
      tgdl download -g 1234567890 --max-size 100MB
      tgdl download -c 1234567890 --limit 50
      tgdl download -c 1234567890 --min-id 20 --max-id 100
      tgdl download -c 1234567890 --concurrent 10
    """
    if concurrent < 1 or concurrent > MAX_CONCURRENT_LIMIT:
        click.echo(click.style(
            f"\u2717 --concurrent must be between 1 and {MAX_CONCURRENT_LIMIT}", fg='red'
        ))
        return

    if not channel and not group and not bot:
        click.echo(click.style("✗ Please specify either --channel, --group, or --bot", fg='red'))
        click.echo("Use 'tgdl channels', 'tgdl groups', or 'tgdl bots' to list available IDs")
        return

    if sum([bool(channel), bool(group), bool(bot)]) > 1:
        click.echo(click.style("✗ Please specify only one: --channel, --group, OR --bot", fg='red'))
        return

    entity_id = channel or group or bot
    entity_type = "channel" if channel else ("group" if group else "bot")

    media_types = []
    if photos:
        media_types.append(MediaType.PHOTO)
    if videos:
        media_types.append(MediaType.VIDEO)
    if audio:
        media_types.append(MediaType.AUDIO)
    if documents:
        media_types.append(MediaType.DOCUMENT)
    if not media_types:
        media_types.append(MediaType.ALL)

    # Fix #2: guard against None from _parse_size in download command
    max_size_bytes = _parse_size(max_size) if max_size else None
    min_size_bytes = _parse_size(min_size) if min_size else None
    if (max_size and max_size_bytes is None) or (min_size and min_size_bytes is None):
        return  # _parse_size already printed the error

    click.echo(click.style(f"\n📥 Download Settings", fg='cyan', bold=True))
    click.echo(f"  Entity: {entity_type.capitalize()} {entity_id}")
    click.echo(f"  Media types: {', '.join([mt.value for mt in media_types])}")
    if min_id or max_id:
        click.echo(f"  Message ID range: {min_id or 'start'} to {max_id or 'latest'}")
    if max_size_bytes:
        click.echo(f"  Max size: {max_size} ({format_bytes(max_size_bytes)})")
    if min_size_bytes:
        click.echo(f"  Min size: {min_size} ({format_bytes(min_size_bytes)})")
    if limit:
        click.echo(f"  Limit: {limit} files")
    click.echo(f"  Parallel downloads: {concurrent}")
    click.echo(f"  Output: {output}")
    click.echo(click.style("\n💡 Tip: Files already downloaded will be skipped automatically", fg='yellow'))
    click.echo(click.style("⚠️  Press Ctrl+C to cancel at any time\n", fg='yellow'))

    if not limit or limit > 100:
        try:
            if not click.confirm("Continue with download?", default=True):
                click.echo(click.style("\n⚠ Download cancelled.", fg='yellow'))
                return
        except (click.Abort, KeyboardInterrupt):
            click.echo(click.style("\n\n⚠ Download cancelled.", fg='yellow'))
            return

    downloader = Downloader(
        max_concurrent=concurrent,
        media_types=media_types,
        max_size=max_size_bytes,
        min_size=min_size_bytes,
        output_dir=output,
    )

    try:
        count = run_async(downloader.download_from_entity(entity_id, limit, min_id, max_id))
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
@require_auth
@click.argument('link')
@click.option('-p', '--photos', is_flag=True, help='Accept only photos')
@click.option('-v', '--videos', is_flag=True, help='Accept only videos')
@click.option('-a', '--audio', is_flag=True, help='Accept only audio files')
@click.option('-d', '--documents', is_flag=True, help='Accept only documents')
@click.option('--max-size', type=str, help='Maximum file size (e.g., 100MB, 1GB)')
@click.option('--min-size', type=str, help='Minimum file size (e.g., 1MB, 10KB)')
@click.option('-o', '--output', type=str, default=DEFAULT_OUTPUT_DIR,
              help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})')
def download_link(link, photos, videos, audio, documents, max_size, min_size, output):
    """
    Download media from a single message link.

    \b
    Examples:
      tgdl download-link https://t.me/channel/123
      tgdl download-link https://t.me/c/1234567890/123
      tgdl download-link https://t.me/channel/123 -v --max-size 100MB
    """
    media_types = []
    if photos:
        media_types.append(MediaType.PHOTO)
    if videos:
        media_types.append(MediaType.VIDEO)
    if audio:
        media_types.append(MediaType.AUDIO)
    if documents:
        media_types.append(MediaType.DOCUMENT)
    if not media_types:
        media_types.append(MediaType.ALL)

    # Fix #2: guard against None from _parse_size in download-link command
    max_size_bytes = _parse_size(max_size) if max_size else None
    min_size_bytes = _parse_size(min_size) if min_size else None
    if (max_size and max_size_bytes is None) or (min_size and min_size_bytes is None):
        return  # _parse_size already printed the error

    downloader = Downloader(
        max_concurrent=1,
        media_types=media_types,
        max_size=max_size_bytes,
        min_size=min_size_bytes,
        output_dir=output,
    )

    click.echo(click.style(f"\n📥 Downloading from link", fg='cyan', bold=True))
    click.echo(f"Link: {link}")
    if max_size_bytes:
        click.echo(f"Max size: {format_bytes(max_size_bytes)}")
    if min_size_bytes:
        click.echo(f"Min size: {format_bytes(min_size_bytes)}")
    click.echo()

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

    is_auth, me = run_async(_check_auth_and_get_user())

    if is_auth:
        click.echo(click.style("✓ Authenticated", fg='green'))
        if me:
            click.echo(f"  Name: {me.first_name}" + (f" {me.last_name}" if me.last_name else ""))
            click.echo(f"  User ID: {me.id}")
            if me.username:
                click.echo(f"  Username: @{me.username}")
    else:
        click.echo(click.style("✗ Not authenticated", fg='red'))
        click.echo("  Run 'tgdl login' to authenticate")

    click.echo(f"\nConfig directory: {config.config_dir}")
    click.echo(f"Session file: {config.session_file}")
    click.echo(f"Progress file: {config.progress_file}")

    api_id, api_hash = config.get_api_credentials()
    if api_id:
        api_id_str = str(api_id)
        masked_id = '*' * max(0, len(api_id_str) - 4) + api_id_str[-4:]
        click.echo(f"\nAPI ID: {masked_id}")
        click.echo(f"API Hash: {'*' * 8}{api_hash[-4:] if api_hash else 'Not set'}")
    else:
        click.echo("\nAPI credentials: Not configured")


if __name__ == '__main__':
    main()
