"""Media downloader module with filters and parallel downloads."""

import os
import re
import asyncio
import logging
import mimetypes
from pathlib import Path
from typing import Optional, List, Set, Callable, Tuple, Union
from enum import Enum

import click
from tqdm.asyncio import tqdm
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    DocumentAttributeVideo,
    DocumentAttributeAudio,
)
from telethon.errors import (
    FloodWaitError,
    ChannelPrivateError,
    FileReferenceExpiredError,
)

from tgdl.auth import get_authenticated_client
from tgdl.config import get_config
from tgdl.utils import format_bytes

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENT = 5
MAX_CONCURRENT_LIMIT = 20
DEFAULT_OUTPUT_DIR = "downloads"
DOWNLOAD_TIMEOUT = 1800
PROGRESS_BAR_LENGTH = 30
PROGRESS_BAR_FILLED_CHAR = "█"
PROGRESS_BAR_EMPTY_CHAR = "░"
MIME_EXTENSION_OVERRIDES = {
    "video/mp4": ".mp4",
    "video/x-matroska": ".mkv",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "application/pdf": ".pdf",
}


def _guess_extension(mime_type: Optional[str]) -> str:
    """Return a stable extension for common MIME types."""
    if not mime_type:
        return ""
    normalized = mime_type.lower()
    if normalized in MIME_EXTENSION_OVERRIDES:
        return MIME_EXTENSION_OVERRIDES[normalized]
    return mimetypes.guess_extension(normalized) or ""


class MediaType(Enum):
    """Media types for filtering."""
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ALL = "all"


class Downloader:
    """Handle media downloads from Telegram."""

    def __init__(
        self,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        media_types: List[MediaType] = None,
        max_size: Optional[int] = None,
        min_size: Optional[int] = None,
        output_dir: str = DEFAULT_OUTPUT_DIR,
    ):
        self.max_concurrent = max_concurrent
        self.media_types = media_types or [MediaType.ALL]
        self.max_size = max_size
        self.min_size = min_size
        self.output_dir = output_dir
        self.config = get_config()

    def _get_media_type(self, message) -> Optional[MediaType]:
        """Determine media type from message."""
        if not message.media:
            return None

        if isinstance(message.media, MessageMediaPhoto):
            return MediaType.PHOTO

        if isinstance(message.media, MessageMediaDocument):
            document = message.media.document
            if not document:
                return None
            for attr in document.attributes:
                if isinstance(attr, DocumentAttributeVideo):
                    return MediaType.VIDEO
                if isinstance(attr, DocumentAttributeAudio):
                    return MediaType.AUDIO
            mime = document.mime_type or ""
            if mime.startswith("video/"):
                return MediaType.VIDEO
            elif mime.startswith("audio/"):
                return MediaType.AUDIO
            elif mime.startswith("image/"):
                return MediaType.PHOTO
            else:
                return MediaType.DOCUMENT

        return None

    def _should_download(self, message) -> bool:
        """Check if message should be downloaded based on filters."""
        if not message.media:
            return False
        if not message.file:
            return False

        media_type = self._get_media_type(message)
        if not media_type:
            return False

        if MediaType.ALL not in self.media_types and media_type not in self.media_types:
            return False

        file_size = message.file.size

        if self.max_size and file_size is not None and file_size > self.max_size:
            return False

        if self.min_size and (file_size is None or file_size < self.min_size):
            return False

        return True

    def _get_downloaded_message_ids(self, folder: Path) -> Set[int]:
        """Get set of message IDs from already downloaded files.

        Fix #16: exclude symlinks — is_file() returns True for symlinks too,
        which could fool the size check with a large linked file.
        """
        if not folder.exists():
            return set()

        message_ids = set()
        for filename in os.listdir(folder):
            file_path = folder / filename
            # Fix #16: skip symlinks explicitly
            if file_path.is_symlink() or not file_path.is_file():
                continue
            try:
                if file_path.stat().st_size == 0:
                    continue
            except OSError:
                continue
            match = re.match(r'^(\d+)', filename)
            if match:
                message_ids.add(int(match.group(1)))

        return message_ids

    async def _download_single(
        self,
        message,
        folder: Path,
        semaphore: asyncio.Semaphore,
        dedup_lock: asyncio.Lock,
        pbar,
        downloaded_message_ids: Set[int],
        client,
        entity_id: int = None,
    ):
        """Download a single media file.

        Fix #15: pbar.update() is now called OUTSIDE the dedup_lock so the
        lock is held only for the minimal check-and-add operation, not during
        any I/O.
        """
        already_done = False
        dest_path: Optional[Path] = None
        try:
            # Atomically check-and-reserve this message ID
            async with dedup_lock:
                if message.id in downloaded_message_ids:
                    already_done = True
                else:
                    downloaded_message_ids.add(message.id)

            if already_done:
                pbar.update(1)  # Fix #15: outside lock
                return None, message.id

            async with semaphore:
                ext = ""
                if message.file and message.file.name:
                    ext = Path(message.file.name).suffix
                elif message.file and message.file.mime_type:
                    ext = _guess_extension(message.file.mime_type)

                dest = str(folder / f"{message.id}{ext}")
                dest_path = Path(dest)

                try:
                    file_path = await asyncio.wait_for(
                        message.download_media(file=dest),
                        timeout=DOWNLOAD_TIMEOUT,
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Download timed out for msg {message.id}")
                    self._cleanup_partial(dest_path)
                    async with dedup_lock:
                        downloaded_message_ids.discard(message.id)
                    pbar.update(1)
                    return None, message.id
                except FileReferenceExpiredError:
                    logger.info(f"File reference expired for msg {message.id}, re-fetching...")
                    try:
                        chat = entity_id if entity_id is not None else message.chat_id
                        fresh_message = await client.get_messages(chat, ids=message.id)
                        if not fresh_message:
                            raise Exception(f"Message {message.id} no longer exists")
                        file_path = await asyncio.wait_for(
                            fresh_message.download_media(file=dest),
                            timeout=DOWNLOAD_TIMEOUT,
                        )
                    except asyncio.TimeoutError as refetch_timeout:
                        logger.error(f"Download timed out for msg {message.id} (re-fetch)")
                        self._cleanup_partial(dest_path)
                        async with dedup_lock:
                            downloaded_message_ids.discard(message.id)
                        raise Exception("Download timed out (on re-fetch)") from refetch_timeout
                    except Exception as refetch_error:
                        logger.error(f"Failed to re-fetch msg {message.id}: {refetch_error}")
                        self._cleanup_partial(dest_path)
                        async with dedup_lock:
                            downloaded_message_ids.discard(message.id)
                        raise refetch_error

            pbar.update(1)  # Fix #15: outside lock

            if file_path:
                return file_path, message.id

            self._cleanup_partial(dest_path)
            async with dedup_lock:
                downloaded_message_ids.discard(message.id)
            return None, message.id

        except Exception as e:
            click.echo(f"\n✗ Error downloading message {message.id}: {e}")
            if dest_path:
                self._cleanup_partial(dest_path)
            async with dedup_lock:
                downloaded_message_ids.discard(message.id)
            pbar.update(1)  # Fix #15: outside lock
            return None, message.id

    async def download_from_entity(
        self,
        entity_id: int,
        limit: Optional[int] = None,
        min_msg_id: Optional[int] = None,
        max_msg_id: Optional[int] = None,
    ) -> int:
        """Download media from a channel or group."""
        client = get_authenticated_client()
        if not client:
            return 0

        try:
            await client.connect()
            return await self._download_from_entity_inner(
                client, entity_id, limit, min_msg_id, max_msg_id
            )
        except KeyboardInterrupt:
            click.echo(click.style("\n\n⚠ Download cancelled by user.", fg="yellow"))
            return 0
        except FloodWaitError as e:
            click.echo(click.style(f"✗ Rate limited by Telegram. Wait {e.seconds} seconds", fg="red"))
            return 0
        except Exception as e:
            click.echo(click.style(f"✗ Download failed: {e}", fg="red"))
            logger.exception(f"Unexpected error during download from entity {entity_id}")
            return 0
        finally:
            try:
                await client.disconnect()
            except Exception as disc_err:
                logger.debug(f"Error disconnecting client: {disc_err}")

    async def _download_from_entity_inner(
        self,
        client,
        entity_id: int,
        limit: Optional[int],
        min_msg_id: Optional[int],
        max_msg_id: Optional[int],
    ) -> int:
        """Core download logic (client already connected)."""
        entity = None
        try:
            async for dialog in client.iter_dialogs():
                if dialog.entity.id == entity_id:
                    entity = dialog.entity
                    break

            if not entity:
                try:
                    entity = await client.get_entity(entity_id)
                except ChannelPrivateError:
                    click.echo(click.style(f"\n✗ Entity {entity_id} is private or you don't have access", fg="red"))
                    return 0
                except FloodWaitError:
                    raise
                except Exception as e:
                    click.echo(click.style(f"\n✗ Entity {entity_id} not found", fg="red"))
                    logger.error(f"Error getting entity {entity_id}: {type(e).__name__}: {e}")
                    click.echo("\n💡 Make sure:")
                    click.echo("  1. You have access to this entity")
                    click.echo("  2. You've interacted with it before")
                    click.echo("  3. Try: tgdl channels / tgdl groups / tgdl bots")
                    return 0

        except FloodWaitError:
            raise
        except Exception as e:
            click.echo(click.style(f"\n✗ Error accessing entity: {e}", fg="red"))
            return 0

        folder = Path(self.output_dir) / f"entity_{entity_id}"
        folder.mkdir(parents=True, exist_ok=True)

        downloaded_message_ids = self._get_downloaded_message_ids(folder)
        if downloaded_message_ids:
            click.echo(click.style(
                f"Found {len(downloaded_message_ids)} already downloaded files, will skip...",
                fg="yellow",
            ))

        last_message_id = self.config.get_progress(str(entity_id))

        if min_msg_id is not None:
            start_id = min_msg_id - 1
            click.echo(f"Fetching messages from entity {entity_id} "
                       f"(ID range: {min_msg_id} to {max_msg_id or 'latest'})...")
        else:
            start_id = last_message_id if last_message_id else 0
            click.echo(f"Fetching messages from entity {entity_id}...")

        messages_to_download = []

        # iter_messages yields newest → oldest (descending ID order).
        # Fix #6: when max_msg_id is given, pass it as offset_id so Telegram
        # starts fetching from that point instead of the very latest message,
        # avoiding unnecessary API round-trips to skip messages above the ceiling.
        iter_kwargs = {"min_id": start_id}
        if max_msg_id is not None:
            # offset_id is exclusive (Telegram returns messages with id < offset_id),
            # so add 1 to include max_msg_id itself.
            iter_kwargs["offset_id"] = max_msg_id + 1

        async for message in client.iter_messages(entity, **iter_kwargs):
            # Belt-and-suspenders guard in case Telegram returns a stray message
            if max_msg_id is not None and message.id > max_msg_id:
                continue

            if min_msg_id is not None and message.id < min_msg_id:
                break

            if self._should_download(message):
                messages_to_download.append(message)
                if limit and len(messages_to_download) >= limit:
                    break

        if not messages_to_download:
            click.echo(click.style("No new media to download!", fg="yellow"))
            return 0

        click.echo(click.style(f"Found {len(messages_to_download)} media files to download", fg="green"))

        semaphore = asyncio.Semaphore(self.max_concurrent)
        dedup_lock = asyncio.Lock()
        pbar = tqdm(total=len(messages_to_download), desc="Downloading", unit="file")

        tasks = [
            self._download_single(msg, folder, semaphore, dedup_lock, pbar, downloaded_message_ids, client, entity_id)
            for msg in messages_to_download
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        pbar.close()

        successful_ids = []
        failed_ids = []
        had_unhandled_failures = False
        for result in results:
            if isinstance(result, Exception):
                had_unhandled_failures = True
                continue
            file_path, msg_id = result
            if file_path:
                successful_ids.append(msg_id)
            elif msg_id in downloaded_message_ids:
                successful_ids.append(msg_id)
            else:
                failed_ids.append(msg_id)

        if successful_ids:
            if failed_ids:
                oldest_failed_id = min(failed_ids)
                progress_candidate = max((last_message_id or 0), oldest_failed_id - 1)
                self.config.set_progress(str(entity_id), progress_candidate)
            elif not had_unhandled_failures:
                self.config.set_progress(str(entity_id), max(successful_ids))

        successful = len(successful_ids)

        click.echo(click.style(f"\n✓ Successfully downloaded {successful} files!", fg="green"))
        click.echo(f"Files saved to: {folder.absolute()}")
        return successful

    async def download_from_link(self, link: str) -> bool:
        """Download media from a single message link.

        Fix #5: track whether connect() was reached so the finally block only
        calls disconnect() when the client was actually connected.
        """
        client = get_authenticated_client()
        if not client:
            return False

        connected = False
        try:
            entity_id, message_id = self._parse_link(link)
            if not entity_id or not message_id:
                click.echo(click.style("✗ Invalid Telegram link format!", fg="red"))
                click.echo("Supported formats:")
                click.echo("  - https://t.me/channel_username/123")
                click.echo("  - https://t.me/c/1234567890/123")
                return False

            await client.connect()
            connected = True  # Fix #5: mark connected only after successful connect()

            message = await client.get_messages(entity_id, ids=message_id)

            if not message:
                click.echo(click.style("✗ Message not found!", fg="red"))
                return False

            if not message.media:
                click.echo(click.style("✗ This message doesn't contain media!", fg="red"))
                return False

            if not self._should_download(message):
                click.echo(click.style("✗ Media doesn't match your filters!", fg="yellow"))
                return False

            folder = Path(self.output_dir) / "single_downloads"
            folder.mkdir(parents=True, exist_ok=True)

            # Dedup: skip if already downloaded
            downloaded_ids = self._get_downloaded_message_ids(folder)
            if message_id in downloaded_ids:
                click.echo(click.style("✓ File already downloaded, skipping.", fg="yellow"))
                return True

            file_name = "unknown"
            file_size = 0
            if message.file:
                file_name = message.file.name or f"file_{message_id}"
                file_size = message.file.size or 0

            click.echo(f"\nFile: {file_name}")
            click.echo(f"Size: {format_bytes(file_size)}")
            click.echo()

            ext = ""
            if message.file and message.file.name:
                ext = Path(message.file.name).suffix
            elif message.file and message.file.mime_type:
                ext = _guess_extension(message.file.mime_type)
            dest = str(folder / f"{message_id}{ext}")

            dest_path = Path(dest)
            try:
                file_path = await asyncio.wait_for(
                    message.download_media(
                        file=dest, progress_callback=self._create_progress_callback()
                    ),
                    timeout=DOWNLOAD_TIMEOUT,
                )
            except FileReferenceExpiredError:
                logger.info(f"File reference expired for msg {message_id}, re-fetching...")
                fresh_message = await client.get_messages(entity_id, ids=message_id)
                if not fresh_message:
                    self._cleanup_partial(dest_path)
                    raise Exception(f"Message {message_id} no longer exists")
                try:
                    file_path = await asyncio.wait_for(
                        fresh_message.download_media(
                            file=dest, progress_callback=self._create_progress_callback()
                        ),
                        timeout=DOWNLOAD_TIMEOUT,
                    )
                except asyncio.TimeoutError:
                    self._cleanup_partial(dest_path)
                    click.echo(click.style("\n✗ Download timed out (on re-fetch).", fg="red"))
                    return False
                if not file_path:
                    self._cleanup_partial(dest_path)
                    click.echo(click.style("\n✗ Re-fetch download returned no file", fg="red"))
                    return False
            except asyncio.TimeoutError:
                self._cleanup_partial(dest_path)
                click.echo(click.style("\n✗ Download timed out.", fg="red"))
                return False
            print()

            if file_path:
                click.echo(click.style(f"\n✓ Successfully downloaded to: {file_path}", fg="green"))
                return True
            else:
                self._cleanup_partial(dest_path)
                click.echo(click.style("\n✗ Failed to download", fg="red"))
                return False

        except KeyboardInterrupt:
            click.echo(click.style("\n\n⚠ Download cancelled by user.", fg="yellow"))
            return False
        except FloodWaitError as e:
            click.echo(click.style(f"\n✗ Rate limited by Telegram. Wait {e.seconds} seconds", fg="red"))
            return False
        except Exception as e:
            click.echo(click.style(f"\n✗ Download failed: {e}", fg="red"))
            logger.exception(f"Unexpected error during download from link: {link}")
            return False
        finally:
            # Fix #5: only disconnect if we actually connected
            if connected:
                try:
                    await client.disconnect()
                except Exception as disc_err:
                    logger.debug(f"Error disconnecting client: {disc_err}")

    @staticmethod
    def _cleanup_partial(dest_path: Path):
        """Remove a partially downloaded file if it exists."""
        try:
            if dest_path.exists():
                dest_path.unlink()
        except OSError as e:
            logger.debug(f"Failed to clean up partial file {dest_path}: {e}")

    def _create_progress_callback(self) -> Callable:
        """Create a progress callback for single-file download progress bars."""
        async def progress_callback(current: int, total: int) -> None:
            percent = (current / total) * 100 if total > 0 else 0
            filled = int(PROGRESS_BAR_LENGTH * current / total) if total > 0 else 0
            bar = PROGRESS_BAR_FILLED_CHAR * filled + PROGRESS_BAR_EMPTY_CHAR * (PROGRESS_BAR_LENGTH - filled)
            print(
                f"\r  [{bar}] {percent:.1f}% | {format_bytes(current)}/{format_bytes(total)}",
                end="", flush=True,
            )
        return progress_callback

    def _parse_link(self, link: str) -> Tuple[Optional[Union[int, str]], Optional[int]]:
        """Parse Telegram message link.

        Supports:
          - https://t.me/c/1234567890/123  (private channel/group)
          - https://t.me/username/123       (public channel)

        Returns (entity_id, message_id) or (None, None) on failure.
        """
        link = link.strip()

        # Strip query string and trailing slashes before matching
        link = re.sub(r'[?#].*$', '', link).rstrip('/')

        # Private channel/group: https://t.me/c/1234567890/123
        match = re.match(r"https?://t\.me/c/(\d+)/(\d+)$", link)
        if match:
            return int("-100" + match.group(1)), int(match.group(2))

        # Public channel: https://t.me/username/123
        match = re.match(r"https?://t\.me/([^/]+)/(\d+)$", link)
        if match:
            username = match.group(1)
            # Reject invite links and other special paths
            if username.startswith('+') or username in ('joinchat', 'addstickers', 'addemoji', 'share'):
                return None, None
            return username, int(match.group(2))

        return None, None
