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

        # Explicit None checks are important: 0 bytes is a valid filter value.
        if self.max_size is not None and file_size is not None and file_size > self.max_size:
            return False

        if self.min_size is not None and (file_size is None or file_size < self.min_size):
            return False

        return True

    def _get_downloaded_message_ids(self, folder: Path) -> Set[int]:
        """Get set of message IDs from already downloaded files.

        Fix #16: exclude symlinks — is_file() returns True for symlinks too,
        which could fool the size check with a large linked file.

        Fix #9: exclude in-progress ".part" files. These are only ever
        renamed to their final name after a fully successful download (see
        _download_single / download_from_link), so a leftover .part file
        always means an incomplete or interrupted download and must never
        be treated as "already downloaded" — otherwise that message would
        be silently and permanently skipped despite never completing.
        """
        if not folder.exists():
            return set()

        message_ids = set()
        for filename in os.listdir(folder):
            if filename.endswith('.part'):
                continue
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

        Fix #9/#14: downloads now write to a "<dest>.part" temp path and are
        renamed to the final name only after a successful, complete
        download. Telethon writes directly to the path it's given with no
        atomicity guarantee of its own, so without this, a hard interrupt
        (process kill, power loss, etc. — anything that skips our own
        exception handlers) could leave a truncated file at the final
        destination. Since _get_downloaded_message_ids() treats any
        non-empty file at the final path as "already downloaded", a
        truncated file would be permanently mistaken for a completed
        download on the next run. Writing under a .part suffix means a hard
        interrupt leaves only a .part file behind, which is never picked up
        by the dedup scan, so the message is correctly retried.
        """
        already_done = False
        dest_path: Optional[Path] = None
        temp_path: Optional[Path] = None
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

                dest_path = folder / f"{message.id}{ext}"
                temp_path = folder / f"{message.id}{ext}.part"
                temp_dest = str(temp_path)

                try:
                    downloaded_path = await asyncio.wait_for(
                        message.download_media(file=temp_dest),
                        timeout=DOWNLOAD_TIMEOUT,
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Download timed out for msg {message.id}")
                    self._cleanup_partial(temp_path)
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
                        downloaded_path = await asyncio.wait_for(
                            fresh_message.download_media(file=temp_dest),
                            timeout=DOWNLOAD_TIMEOUT,
                        )
                    except asyncio.TimeoutError as refetch_timeout:
                        logger.error(f"Download timed out for msg {message.id} (re-fetch)")
                        self._cleanup_partial(temp_path)
                        async with dedup_lock:
                            downloaded_message_ids.discard(message.id)
                        raise asyncio.TimeoutError(
                            f"Download timed out for msg {message.id} (re-fetch)"
                        ) from refetch_timeout
                    except Exception as refetch_error:
                        logger.error(f"Failed to re-fetch msg {message.id}: {refetch_error}")
                        self._cleanup_partial(temp_path)
                        async with dedup_lock:
                            downloaded_message_ids.discard(message.id)
                        raise refetch_error

                # Fix #9/#14: only now, with a confirmed-complete download in
                # hand, promote the .part file to its final name. os.replace
                # is atomic on both POSIX and Windows, so a crash right at
                # this point either leaves the .part file (retried next run)
                # or the final file (correctly recognized as done) — never a
                # half-renamed state.
                file_path = None
                if downloaded_path and temp_path.exists():
                    try:
                        os.replace(temp_path, dest_path)
                        file_path = str(dest_path)
                    except OSError as rename_err:
                        logger.error(f"Failed to finalize download for msg {message.id}: {rename_err}")
                        self._cleanup_partial(temp_path)

            pbar.update(1)  # Fix #15: outside lock

            if file_path:
                return file_path, message.id

            self._cleanup_partial(temp_path)
            async with dedup_lock:
                downloaded_message_ids.discard(message.id)
            return None, message.id

        except asyncio.CancelledError:
            # Fix #8: on cancellation, release this message's dedup
            # reservation instead of leaving it permanently marked
            # "downloaded" in memory for the rest of this run. Cancellation
            # must still propagate (never swallow CancelledError), and we
            # avoid awaiting the lock here since the event loop may already
            # be tearing down during cancellation — a direct discard is
            # safe because it's a single non-blocking set operation.
            downloaded_message_ids.discard(message.id)
            if temp_path:
                self._cleanup_partial(temp_path)
            raise
        except Exception as e:
            click.echo(f"\n✗ Error downloading message {message.id}: {e}")
            if temp_path:
                self._cleanup_partial(temp_path)
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

        # Fix #9/#14: sweep any .part files left over from a previous run
        # that was killed hard enough to skip our own cleanup handlers (e.g.
        # SIGKILL, power loss). Safe to do unconditionally here because no
        # download for this entity is in progress yet at this point.
        self._cleanup_stale_partials(folder)

        downloaded_message_ids = self._get_downloaded_message_ids(folder)
        preexisting_downloaded_ids = set(downloaded_message_ids)
        if downloaded_message_ids:
            click.echo(click.style(
                f"Found {len(downloaded_message_ids)} already downloaded files, will skip...",
                fg="yellow",
            ))

        last_message_id = self.config.get_progress(str(entity_id))

        if min_msg_id is not None or max_msg_id is not None:
            # Fix #2: a manual range always starts from min_msg_id (or the
            # very beginning if only --max-id was given) and never from the
            # automatic resume watermark — the two are intentionally kept
            # independent so this explicit request cannot corrupt normal
            # resume behavior.
            start_id = (min_msg_id - 1) if min_msg_id is not None else 0
            click.echo(f"Fetching messages from entity {entity_id} "
                       f"(ID range: {min_msg_id or 'start'} to {max_msg_id or 'latest'})...")
            click.echo(click.style(
                "  Note: manual ID-range downloads do not affect the normal auto-resume position.",
                fg="cyan",
            ))
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
            elif msg_id in preexisting_downloaded_ids:
                # Already downloaded before this run; treat as successful for watermark purposes.
                successful_ids.append(msg_id)
            else:
                failed_ids.append(msg_id)

        # Fix #2: only normal (non-range) downloads are allowed to move the
        # automatic resume watermark. A manual --min-id/--max-id run is an
        # explicit, one-off request for a specific slice of history — letting
        # it write to the same watermark as normal `tgdl download -c CHANNEL`
        # runs could rewind or skip the automatic resume position (e.g.
        # re-running an old range would push the watermark backwards, or a
        # --max-id run capped below the real watermark would silently move it
        # back). Manual ranges rely entirely on the on-disk dedup check
        # (_get_downloaded_message_ids) to avoid duplicate downloads instead.
        is_manual_range = min_msg_id is not None or max_msg_id is not None

        if successful_ids and not is_manual_range:
            if failed_ids:
                oldest_failed_id = min(failed_ids)
                # Keep watermark just before the oldest failure so retries include that failed
                # message (min_id is exclusive, hence -1). Telegram IDs are monotonically
                # increasing, so any value below the failed ID is safe even if gaps exist.
                # If the oldest failure is message 1, we store 0 to start from the beginning.
                progress_candidate = max(0, oldest_failed_id - 1)
                self.config.set_progress(str(entity_id), progress_candidate)
            elif not had_unhandled_failures:
                # No failures: safe to advance to the newest successfully handled message.
                self.config.set_progress(str(entity_id), max(successful_ids))
            # When failures lack an ID, leave progress unchanged to avoid skipping retries.

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

            # Message IDs are only unique within a chat. Keep each link
            # download in a per-entity directory so message 123 in chat A
            # can never collide with message 123 in chat B. Prefer the
            # resolved numeric chat_id because public usernames can change.
            resolved_entity_id = getattr(message, "chat_id", None) or entity_id
            entity_key = re.sub(r"[^A-Za-z0-9_-]+", "_", str(resolved_entity_id))
            folder = Path(self.output_dir) / "single_downloads" / f"entity_{entity_key}"
            folder.mkdir(parents=True, exist_ok=True)
            self._cleanup_stale_partials(folder)  # Fix #9/#14

            # Dedup is scoped to this entity directory. Message IDs are not
            # globally unique across Telegram chats/channels.
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
            dest_path = folder / f"{message_id}{ext}"
            temp_path = folder / f"{message_id}{ext}.part"
            temp_dest = str(temp_path)

            # Fix #9/#14: download to a .part file, rename to the final name
            # only on confirmed success (see _download_single for rationale).
            try:
                downloaded_path = await asyncio.wait_for(
                    message.download_media(
                        file=temp_dest, progress_callback=self._create_progress_callback()
                    ),
                    timeout=DOWNLOAD_TIMEOUT,
                )
            except FileReferenceExpiredError:
                logger.info(f"File reference expired for msg {message_id}, re-fetching...")
                fresh_message = await client.get_messages(entity_id, ids=message_id)
                if not fresh_message:
                    self._cleanup_partial(temp_path)
                    raise Exception(f"Message {message_id} no longer exists")
                try:
                    downloaded_path = await asyncio.wait_for(
                        fresh_message.download_media(
                            file=temp_dest, progress_callback=self._create_progress_callback()
                        ),
                        timeout=DOWNLOAD_TIMEOUT,
                    )
                except asyncio.TimeoutError:
                    self._cleanup_partial(temp_path)
                    click.echo(click.style("\n✗ Download timed out (on re-fetch).", fg="red"))
                    return False
                if not downloaded_path:
                    self._cleanup_partial(temp_path)
                    click.echo(click.style("\n✗ Re-fetch download returned no file", fg="red"))
                    return False
            except asyncio.TimeoutError:
                self._cleanup_partial(temp_path)
                click.echo(click.style("\n✗ Download timed out.", fg="red"))
                return False
            print()

            file_path = None
            if downloaded_path and temp_path.exists():
                try:
                    os.replace(temp_path, dest_path)
                    file_path = str(dest_path)
                except OSError as rename_err:
                    logger.error(f"Failed to finalize download for msg {message_id}: {rename_err}")
                    self._cleanup_partial(temp_path)

            if file_path:
                click.echo(click.style(f"\n✓ Successfully downloaded to: {file_path}", fg="green"))
                return True
            else:
                self._cleanup_partial(temp_path)
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
    def _cleanup_partial(dest_path: Optional[Path]):
        """Remove a partially downloaded file if it exists."""
        if not dest_path:
            return
        try:
            if dest_path.exists():
                dest_path.unlink()
        except OSError as e:
            logger.debug(f"Failed to clean up partial file {dest_path}: {e}")

    @staticmethod
    def _cleanup_stale_partials(folder: Path) -> None:
        """Remove any leftover .part files in folder before a new run starts.

        Fix #9/#14: these can only exist if a previous download was
        interrupted hard enough to bypass our normal exception-handling
        cleanup (e.g. SIGKILL, crash, power loss). They're always safe to
        remove at the start of a run since no download is in progress yet.
        """
        if not folder.exists():
            return
        try:
            entries = os.listdir(folder)
        except OSError as e:
            logger.debug(f"Could not scan {folder} for stale .part files: {e}")
            return
        for filename in entries:
            if filename.endswith('.part'):
                Downloader._cleanup_partial(folder / filename)

    def _create_progress_callback(self) -> Callable:
        """Create a progress callback for single-file download progress bars.

        Fix #1: this must be a plain synchronous callback. Telethon calls
        download progress callbacks directly (it does not await them), so an
        `async def` here would never actually run its body — the coroutine
        object gets created and silently discarded, producing no progress
        output and (depending on Python version) an "coroutine was never
        awaited" warning.
        """
        def progress_callback(current: int, total: int) -> None:
            percent = (current / total) * 100 if total > 0 else 0
            filled = int(PROGRESS_BAR_LENGTH * current / total) if total > 0 else 0
            bar = PROGRESS_BAR_FILLED_CHAR * filled + PROGRESS_BAR_EMPTY_CHAR * (PROGRESS_BAR_LENGTH - filled)
            print(
                f"\r  [{bar}] {percent:.1f}% | {format_bytes(current)}/{format_bytes(total)}",
                end="", flush=True,
            )
        return progress_callback

    def _parse_link(self, link: str) -> Tuple[Optional[Union[int, str]], Optional[int]]:
        """Parse a Telegram message link.

        Supports common public/private post URLs on t.me, www.t.me,
        telegram.me, and www.telegram.me, including query strings/fragments.

        Returns (entity_id, message_id) or (None, None) on failure.
        """
        from urllib.parse import urlparse

        raw_link = link.strip()
        if not raw_link:
            return None, None

        try:
            parsed = urlparse(raw_link)
        except ValueError:
            return None, None

        if parsed.scheme.lower() != "https" or parsed.netloc.lower() not in {
            "t.me", "www.t.me", "telegram.me", "www.telegram.me"
        }:
            return None, None

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 3 and parts[0].lower() == "c" and parts[1].isdigit() and parts[2].isdigit():
            return int("-100" + parts[1]), int(parts[2])

        if len(parts) == 3 and parts[0].lower() == "s" and parts[2].isdigit():
            username = parts[1]
            if self._is_reserved_link_username(username):
                return None, None
            return username, int(parts[2])

        if len(parts) == 2 and parts[1].isdigit():
            username = parts[0]
            if self._is_reserved_link_username(username):
                return None, None
            return username, int(parts[1])

        return None, None

    @staticmethod
    def _is_reserved_link_username(username: str) -> bool:
        """Return True for Telegram paths that are not public chat usernames."""
        return username.startswith("+") or username.lower() in {
            "joinchat", "addstickers", "addemoji", "share", "proxy", "iv", "login"
        }
