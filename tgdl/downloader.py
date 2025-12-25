"""Media downloader module with filters and parallel downloads."""

import os
import re
import asyncio
from pathlib import Path
from typing import Optional, List, Set
from enum import Enum

import click
from tqdm.asyncio import tqdm
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    DocumentAttributeVideo,
    DocumentAttributeAudio,
)

from tgdl.auth import get_authenticated_client
from tgdl.config import get_config
from tgdl.utils import format_bytes


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
        max_concurrent: int = 5,
        media_types: List[MediaType] = None,
        max_size: Optional[int] = None,
        min_size: Optional[int] = None,
        output_dir: str = "downloads",
    ):
        """
        Initialize downloader.
        
        Args:
            max_concurrent: Number of parallel downloads
            media_types: List of media types to download
            max_size: Maximum file size in bytes
            min_size: Minimum file size in bytes
            output_dir: Output directory for downloads
        """
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
            
            # Skip if document is None (web pages, etc.)
            if not document:
                return None
            
            # Check attributes
            for attr in document.attributes:
                if isinstance(attr, DocumentAttributeVideo):
                    return MediaType.VIDEO
                if isinstance(attr, DocumentAttributeAudio):
                    return MediaType.AUDIO
            
            # Check MIME type
            mime = document.mime_type or ""
            if mime.startswith("video/"):
                return MediaType.VIDEO
            elif mime.startswith("audio/"):
                return MediaType.AUDIO
            elif mime.startswith("image/"):
                return MediaType.PHOTO
            else:
                return MediaType.DOCUMENT

        # Handle other media types (return DOCUMENT for downloadable media)
        return None

    def _should_download(self, message) -> bool:
        """Check if message should be downloaded based on filters."""
        if not message.media:
            return False
        
        # Must have an actual file to download
        if not message.file:
            return False

        # Check media type filter
        media_type = self._get_media_type(message)
        if not media_type:
            return False
            
        if MediaType.ALL not in self.media_types and media_type not in self.media_types:
            return False

        # Check file size
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
        """Get set of message IDs from already downloaded files."""
        if not folder.exists():
            return set()
        
        message_ids = set()
        for filename in os.listdir(folder):
            # Try to extract message ID from filename
            # Files are named like: <message_id><ext> or <original_name>
            # Check if filename starts with a number (message ID)
            import re
            match = re.match(r'^(\d+)', filename)
            if match:
                message_ids.add(int(match.group(1)))
        
        return message_ids

    async def _download_single(
        self, message, folder: Path, semaphore, pbar, downloaded_message_ids: Set[int]
    ):
        """Download a single media file."""
        try:
            # Skip if message ID already downloaded
            if message.id in downloaded_message_ids:
                pbar.update(1)
                return None, message.id

            # Download with semaphore (allows parallel downloads)
            async with semaphore:
                file_path = await message.download_media(file=str(folder))
            
            # Add to downloaded set after successful download
            if file_path:
                downloaded_message_ids.add(message.id)
            
            pbar.update(1)

            if file_path:
                return file_path, message.id
            return None, message.id

        except Exception as e:
            click.echo(f"\n✗ Error downloading message {message.id}: {e}")
            pbar.update(1)
            return None, message.id

    async def download_from_entity(
        self, entity_id: int, limit: Optional[int] = None, min_msg_id: Optional[int] = None, max_msg_id: Optional[int] = None
    ) -> int:
        """
        Download media from a channel or group.
        
        Args:
            entity_id: Channel or group ID
            limit: Maximum number of files to download (None for all)
            min_msg_id: Minimum message ID to start from (inclusive)
            max_msg_id: Maximum message ID to stop at (inclusive)
            
        Returns:
            Number of files successfully downloaded
        """
        client = get_authenticated_client()
        if not client:
            return 0

        try:
            await client.connect()
            
            # Get the entity from dialogs to ensure it's properly resolved
            entity = None
            try:
                # Get all dialogs and search for the entity
                async for dialog in client.iter_dialogs():
                    if dialog.entity.id == entity_id:
                        entity = dialog.entity
                        break
                
                # If not found in dialogs, try to get it directly
                if not entity:
                    try:
                        entity = await client.get_entity(entity_id)
                    except Exception:
                        click.echo(click.style(f"\n✗ Entity {entity_id} not found", fg="red"))
                        click.echo("\n💡 Make sure:")
                        click.echo(f"  1. You have access to this entity")
                        click.echo(f"  2. You've interacted with it before")
                        click.echo(f"  3. Try these commands to find the correct ID:")
                        click.echo(f"     • tgdl channels - List all your channels")
                        click.echo(f"     • tgdl groups - List all your groups")
                        click.echo(f"     • tgdl bots - List all your bot chats")
                        await client.disconnect()
                        return 0
                    
            except Exception as e:
                click.echo(click.style(f"\n✗ Error accessing entity: {e}", fg="red"))
                await client.disconnect()
                return 0

            # Create output directory
            folder = Path(self.output_dir) / f"entity_{entity_id}"
            folder.mkdir(parents=True, exist_ok=True)

            # Get already downloaded message IDs
            downloaded_message_ids = self._get_downloaded_message_ids(folder)
            if downloaded_message_ids:
                click.echo(
                    click.style(
                        f"Found {len(downloaded_message_ids)} already downloaded files, will skip...",
                        fg="yellow",
                    )
                )

            # Get last progress (only if no custom range specified)
            last_message_id = self.config.get_progress(str(entity_id))
            
            # Determine the starting point
            if min_msg_id is not None:
                start_id = min_msg_id - 1  # min_id is exclusive, so subtract 1 to include min_msg_id
                click.echo(f"Fetching messages from entity {entity_id} (ID range: {min_msg_id} to {max_msg_id or 'latest'})...")
            else:
                start_id = last_message_id if last_message_id else 0
                click.echo(f"Fetching messages from entity {entity_id}...")

            # Collect messages with media
            messages_to_download = []
            # Use min_id to get messages AFTER the last downloaded one
            # This way we only fetch NEW messages since last download
            async for message in client.iter_messages(
                entity, min_id=start_id
            ):
                # If max_msg_id is specified, stop when we reach it
                if max_msg_id is not None and message.id > max_msg_id:
                    continue
                
                # If min_msg_id is specified and message is below it, we've gone past the range
                if min_msg_id is not None and message.id < min_msg_id:
                    break
                
                if self._should_download(message):
                    messages_to_download.append(message)
                    
                    # Check limit
                    if limit and len(messages_to_download) >= limit:
                        break

            if not messages_to_download:
                click.echo(click.style("No new media to download!", fg="yellow"))
                await client.disconnect()
                return 0

            click.echo(
                click.style(
                    f"Found {len(messages_to_download)} media files to download",
                    fg="green",
                )
            )

            # Download with concurrency
            semaphore = asyncio.Semaphore(self.max_concurrent)
            pbar = tqdm(total=len(messages_to_download), desc="Downloading", unit="file")

            tasks = [
                self._download_single(msg, folder, semaphore, pbar, downloaded_message_ids)
                for msg in messages_to_download
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            pbar.close()

            # Save progress
            if messages_to_download:
                self.config.set_progress(str(entity_id), messages_to_download[-1].id)

            # Count successful downloads
            successful = sum(
                1 for result in results 
                if not isinstance(result, Exception) and result[0] is not None
            )

            click.echo(
                click.style(f"\n✓ Successfully downloaded {successful} files!", fg="green")
            )
            click.echo(f"Files saved to: {folder.absolute()}")

            await client.disconnect()
            return successful

        except Exception as e:
            click.echo(click.style(f"✗ Download failed: {e}", fg="red"))
            try:
                await client.disconnect()
            except Exception:
                pass
            return 0

    async def download_from_link(self, link: str) -> bool:
        """
        Download media from a single message link.
        
        Args:
            link: Telegram message link
            
        Returns:
            True if successful, False otherwise
        """
        client = get_authenticated_client()
        if not client:
            return False

        try:
            # Parse link
            entity_id, message_id = self._parse_link(link)
            if not entity_id or not message_id:
                click.echo(click.style("✗ Invalid Telegram link format!", fg="red"))
                click.echo("Supported formats:")
                click.echo("  - https://t.me/channel_username/123")
                click.echo("  - https://t.me/c/1234567890/123")
                return False

            await client.connect()

            # Get message
            message = await client.get_messages(entity_id, ids=message_id)

            if not message:
                click.echo(click.style("✗ Message not found!", fg="red"))
                await client.disconnect()
                return False

            if not message.media:
                click.echo(click.style("✗ This message doesn't contain media!", fg="red"))
                await client.disconnect()
                return False

            # Check filters
            if not self._should_download(message):
                click.echo(
                    click.style("✗ Media doesn't match your filters!", fg="yellow")
                )
                await client.disconnect()
                return False

            # Create output directory
            folder = Path(self.output_dir) / "single_downloads"
            folder.mkdir(parents=True, exist_ok=True)

            # Get file info
            file_name = "unknown"
            file_size = 0
            if message.file:
                file_name = message.file.name or f"file_{message_id}"
                file_size = message.file.size

            click.echo(f"\nFile: {file_name}")
            click.echo(f"Size: {format_bytes(file_size)}")
            click.echo()

            # Progress callback with better formatting
            async def progress_callback(current, total):
                percent = (current / total) * 100 if total > 0 else 0
                bar_length = 30
                filled = int(bar_length * current / total) if total > 0 else 0
                bar = "█" * filled + "░" * (bar_length - filled)
                
                print(
                    f"\r  [{bar}] {percent:.1f}% | {format_bytes(current)}/{format_bytes(total)}",
                    end="",
                    flush=True,
                )

            file_path = await message.download_media(
                file=str(folder), progress_callback=progress_callback
            )

            print()  # New line after progress

            if file_path:
                click.echo(click.style(f"\n✓ Successfully downloaded to: {file_path}", fg="green"))
                await client.disconnect()
                return True
            else:
                click.echo(click.style("\n✗ Failed to download", fg="red"))
                await client.disconnect()
                return False

        except Exception as e:
            click.echo(click.style(f"\n✗ Download failed: {e}", fg="red"))
            try:
                await client.disconnect()
            except Exception:
                pass
            return False

    def _parse_link(self, link: str):
        """Parse Telegram message link."""
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
