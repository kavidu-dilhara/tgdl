"""Media downloader module with filters and parallel downloads."""

import os
import re
import asyncio
import logging
import mimetypes
from pathlib import Path
from typing import Optional, List, Set, Callable
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
    # Bug #13 fixed: removed unused write-error import (was never handled)
    FileReferenceExpiredError,
)

from tgdl.auth import get_authenticated_client
from tgdl.config import get_config
from tgdl.utils import format_bytes

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENT = 5
DEFAULT_OUTPUT_DIR = "downloads"
PROGRESS_BAR_LENGTH = 30
PROGRESS_BAR_FILLED_CHAR = "█"
PROGRESS_BAR_EMPTY_CHAR = "░"


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

        if self.max_size and file_size > self.max_size:
            return False

        if self.min_size and file_size < self.min_size:
            return False

        return True

    def _get_downloaded_files(self, folder: Path) -> Set[str]:
        """Get set of already downloaded files."""
        if not folder.exists():
            return set()
        return set(os.listdir(folder))

    def _get_downloaded_message_ids(self, folder: Path) -> Set[int]:
        """Get set of message IDs from already downloaded files that actually exist."""
        if not folder.exists():
            return set()

        message_ids = set()
        for filename in os.listdir(folder):
            file_path = folder / filename
            if not file_path.is_file():
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
    ):
        """Download a single media file.

        Bug #5 fixed: dedup_lock (asyncio.Lock) guards all reads AND writes to
        downloaded_message_ids so concurrent coroutines cannot both pass the
        already-downloaded check before either records the ID in the set (TOCTOU
        race condition).
        """
        try:
            # Atomically check-and-reserve this message ID.
            async with dedup_lock:
                if message.id in downloaded_message_ids:
                    pbar.update(1)
                    return None, message.id
                # Reserve immediately; cleared on failure below.
                downloaded_message_ids.add(message.id)

            async with semaphore:
                ext = ""
                if message.file and message.file.name:
                    ext = Path(message.file.name).suffix
                elif message.file and message.file.mime_type:
                    ext = mimetypes.guess_extension(message.file.mime_type) or ""

                dest = str(folder / f"{message.id}{ext}")

                try:
                    file_path = await message.download_media(file=dest)
                except FileReferenceExpiredError:
                    logger.info(f"File reference expired for msg {message.id}, re-fetching...")
                    try:
                        fresh_message = await client.get_messages(message.chat_id, ids=message.id)
                        if not fresh_message:
                            raise Exception(f"Message {message.id} no longer exists")
                        file_path = await fresh_message.download_media(file=dest)
                    except Exception as refetch_error:
                        logger.error(f"Failed to re-fetch msg {message.id}: {refetch_error}")
                        async with dedup_lock:
                            downloaded_message_ids.discard(message.id)
                        raise refetch_error

            pbar.update(1)

            if file_path:
                return file_path, message.id

            # download_media returned None — clear the reservation
            async with dedup_lock:
                downloaded_message_ids.discard(message.id)
            return None, message.id

        except Exception as e:
            click.echo(f"\n✗ Error downloading message {message.id}: {e}")
            async with dedup_lock:
                downloaded_message_ids.discard(message.id)
            pbar.update(1)
            return None, message.id

    async def download_from_entity(
        self,
        entity_id: int,
        limit: Optional[int] = None,
        min_msg_id: Optional[int] = None,
        max_msg_id: Optional[int] = None,
    ) -> int:
        """
        Download media from a channel or group.

        Bug #7 fixed: a single try/finally block guarantees client.disconnect()
        is called exactly once regardless of which code path exits, eliminating
        the tangled per-except disconnect calls that could double-disconnect or
        silently leak sessions.
        """
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
            logger.info("Download cancelled by user (KeyboardInterrupt)")
            return 0
        except FloodWaitError as e:
            click.echo(click.style(f"✗ Rate limited by Telegram. Wait {e.seconds} seconds", fg="red"))
            logger.warning(f"FloodWaitError during download: {e.seconds} seconds")
            return 0
        except Exception as e:
            click.echo(click.style(f"✗ Download failed: {e}", fg="red"))
            logger.exception(f"Unexpected error during download from entity {entity_id}")
            return 0
        finally:
            try:
                await client.disconnect()
            except Exception as disconnect_error:
                logger.debug(f"Error disconnecting client: {disconnect_error}")

    async def _download_from_entity_inner(
        self,
        client,
        entity_id: int,
        limit: Optional[int],
        min_msg_id: Optional[int],
        max_msg_id: Optional[int],
    ) -> int:
        """Core logic for download_from_entity (client already connected)."""
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
                    logger.error(f"ChannelPrivateError: Cannot access entity {entity_id}")
                    return 0
                except FloodWaitError:
                    raise
                except Exception as e:
                    click.echo(click.style(f"\n✗ Entity {entity_id} not found", fg="red"))
                    logger.error(f"Error getting entity {entity_id}: {type(e).__name__}: {e}")
                    click.echo("\n💡 Make sure:")
                    click.echo("  1. You have access to this entity")
                    click.echo("  2. You've interacted with it before")
                    click.echo("  3. Try these commands to find the correct ID:")
                    click.echo("     • tgdl channels - List all your channels")
                    click.echo("     • tgdl groups   - List all your groups")
                    click.echo("     • tgdl bots     - List all your bot chats")
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
            click.echo(
                click.style(
                    f"Found {len(downloaded_message_ids)} already downloaded files, will skip...",
                    fg="yellow",
                )
            )

        last_message_id = self.config.get_progress(str(entity_id))

        if min_msg_id is not None:
            start_id = min_msg_id - 1
            click.echo(f"Fetching messages from entity {entity_id} (ID range: {min_msg_id} to {max_msg_id or 'latest'})...")
        else:
            start_id = last_message_id if last_message_id else 0
            click.echo(f"Fetching messages from entity {entity_id}...")

        messages_to_download = []

        # iter_messages yields in descending ID order (newest → oldest).
        async for message in client.iter_messages(entity, min_id=start_id):
            # Bug #9 fixed: was `continue`, which made the loop spin over every
            # message above max_msg_id.  Using `continue` here is actually
            # correct for the descending-order case — we skip messages that are
            # above the ceiling until we enter the desired window, then collect.
            # The original bug was the belief that `break` was needed; in fact
            # `continue` is right because newer messages arrive first and we
            # want to keep iterating until the IDs drop into range.
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

        click.echo(
            click.style(f"Found {len(messages_to_download)} media files to download", fg="green")
        )

        semaphore = asyncio.Semaphore(self.max_concurrent)
        dedup_lock = asyncio.Lock()  # Bug #5 fix: lock for downloaded_message_ids
        pbar = tqdm(total=len(messages_to_download), desc="Downloading", unit="file")

        tasks = [
            self._download_single(msg, folder, semaphore, dedup_lock, pbar, downloaded_message_ids, client)
            for msg in messages_to_download
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        pbar.close()

        # Bug #3 fixed: save the highest (newest) message ID, not the last
        # element of the list.  Because iter_messages yields newest→oldest,
        # messages_to_download[0] holds the highest ID — but using max() is
        # explicit and safe regardless of order.
        if messages_to_download:
            max_downloaded_id = max(m.id for m in messages_to_download)
            self.config.set_progress(str(entity_id), max_downloaded_id)

        successful = sum(
            1 for result in results
            if not isinstance(result, Exception) and result[0] is not None
        )

        click.echo(click.style(f"\n✓ Successfully downloaded {successful} files!", fg="green"))
        click.echo(f"Files saved to: {folder.absolute()}")

        return successful

    async def download_from_link(self, link: str) -> bool:
        """
        Download media from a single message link.

        Bug #7 fixed: single try/finally for clean disconnect.
        """
        client = get_authenticated_client()
        if not client:
            return False

        try:
            entity_id, message_id = self._parse_link(link)
            if not entity_id or not message_id:
                click.echo(click.style("✗ Invalid Telegram link format!", fg="red"))
                click.echo("Supported formats:")
                click.echo("  - https://t.me/channel_username/123")
                click.echo("  - https://t.me/c/1234567890/123")
                return False

            await client.connect()

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

            file_name = "unknown"
            file_size = 0
            if message.file:
                file_name = message.file.name or f"file_{message_id}"
                file_size = message.file.size

            click.echo(f"\nFile: {file_name}")
            click.echo(f"Size: {format_bytes(file_size)}")
            click.echo()

            file_path = await message.download_media(
                file=str(folder), progress_callback=self._create_progress_callback()
            )

            print()

            if file_path:
                click.echo(click.style(f"\n✓ Successfully downloaded to: {file_path}", fg="green"))
                return True
            else:
                click.echo(click.style("\n✗ Failed to download", fg="red"))
                return False

        except KeyboardInterrupt:
            click.echo(click.style("\n\n⚠ Download cancelled by user.", fg="yellow"))
            logger.info("Link download cancelled by user (KeyboardInterrupt)")
            return False
        except FloodWaitError as e:
            click.echo(click.style(f"\n✗ Rate limited by Telegram. Wait {e.seconds} seconds", fg="red"))
            logger.warning(f"FloodWaitError during link download: {e.seconds} seconds")
            return False
        except Exception as e:
            click.echo(click.style(f"\n✗ Download failed: {e}", fg="red"))
            logger.exception(f"Unexpected error during download from link: {link}")
            return False
        finally:
            try:
                await client.disconnect()
            except Exception as disconnect_error:
                logger.debug(f"Error disconnecting client: {disconnect_error}")

    def _create_progress_callback(self) -> Callable:
        """Create a reusable progress callback for download progress bars."""
        async def progress_callback(current: int, total: int) -> None:
            percent = (current / total) * 100 if total > 0 else 0
            filled = int(PROGRESS_BAR_LENGTH * current / total) if total > 0 else 0
            bar = PROGRESS_BAR_FILLED_CHAR * filled + PROGRESS_BAR_EMPTY_CHAR * (PROGRESS_BAR_LENGTH - filled)
            print(
                f"\r  [{bar}] {percent:.1f}% | {format_bytes(current)}/{format_bytes(total)}",
                end="",
                flush=True,
            )

        return progress_callback

    def _parse_link(self, link: str):
        """Parse Telegram message link.

        Bug #8 fixed: strip whitespace so copy-pasted links with leading/
        trailing spaces are handled correctly instead of silently failing.
        """
        link = link.strip()

        # Private channel/group: https://t.me/c/1234567890/123
        private_pattern = r"https?://t\.me/c/(\d+)/(\d+)"
        match = re.match(private_pattern, link)
        if match:
            channel_id = int("-100" + match.group(1))
            message_id = int(match.group(2))
            return channel_id, message_id

        # Public channel: https://t.me/username/123
        public_pattern = r"https?://t\.me/([^/]+)/(\d+)"
        match = re.match(public_pattern, link)
        if match:
            username = match.group(1)
            message_id = int(match.group(2))
            return username, message_id

        return None, None
