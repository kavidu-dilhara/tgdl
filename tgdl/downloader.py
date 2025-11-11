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

        return None

    def _should_download(self, message) -> bool:
        """Check if message should be downloaded based on filters."""
        if not message.media:
            return False

        # Check media type filter
        media_type = self._get_media_type(message)
        if MediaType.ALL not in self.media_types and media_type not in self.media_types:
            return False

        # Check file size
        if message.file:
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

    async def _download_single(
        self, message, folder: Path, semaphore, pbar, downloaded_files: Set[str]
    ):
        """Download a single media file."""
        async with semaphore:
            try:
                # Get filename
                file_name = None
                if message.file:
                    file_name = message.file.name or f"{message.id}{message.file.ext}"

                # Skip if already downloaded
                if file_name and file_name in downloaded_files:
                    pbar.update(1)
                    return None, message.id

                # Download
                file_path = await message.download_media(file=str(folder))
                pbar.update(1)

                if file_path:
                    return file_path, message.id
                return None, message.id

            except Exception as e:
                click.echo(f"\n✗ Error downloading message {message.id}: {e}")
                pbar.update(1)
                return None, message.id

    async def download_from_entity(
        self, entity_id: int, limit: Optional[int] = None
    ) -> int:
        """
        Download media from a channel or group.
        
        Args:
            entity_id: Channel or group ID
            limit: Maximum number of files to download (None for all)
            
        Returns:
            Number of files successfully downloaded
        """
        client = get_authenticated_client()
        if not client:
            return 0

        try:
            await client.connect()

            # Create output directory
            folder = Path(self.output_dir) / f"entity_{entity_id}"
            folder.mkdir(parents=True, exist_ok=True)

            # Get already downloaded files
            downloaded_files = self._get_downloaded_files(folder)
            if downloaded_files:
                click.echo(
                    click.style(
                        f"Found {len(downloaded_files)} already downloaded files, skipping...",
                        fg="yellow",
                    )
                )

            # Get last progress
            last_message_id = self.config.get_progress(str(entity_id))

            click.echo(f"Fetching messages from entity {entity_id}...")

            # Collect messages with media
            messages_to_download = []
            async for message in client.iter_messages(
                entity_id, offset_id=last_message_id, reverse=True
            ):
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
                self._download_single(msg, folder, semaphore, pbar, downloaded_files)
                for msg in messages_to_download
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            pbar.close()

            # Save progress
            if messages_to_download:
                self.config.set_progress(str(entity_id), messages_to_download[-1].id)

            # Count successful downloads
            successful = sum(
                1 for file_path, _ in results 
                if file_path and not isinstance(file_path, Exception)
            )

            click.echo(
                click.style(f"\n✓ Successfully downloaded {successful} files!", fg="green")
            )
            click.echo(f"Files saved to: {folder.absolute()}")

            await client.disconnect()
            return successful

        except Exception as e:
            click.echo(click.style(f"✗ Download failed: {e}", fg="red"))
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
            file_size_mb = 0
            if message.file:
                file_name = message.file.name or f"file_{message_id}"
                file_size_mb = message.file.size / (1024 * 1024)

            click.echo(f"File: {file_name}")
            click.echo(f"Size: {file_size_mb:.2f} MB")
            click.echo("Downloading...")

            # Progress callback
            async def progress_callback(current, total):
                percent = (current / total) * 100 if total > 0 else 0
                downloaded_mb = current / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                print(
                    f"\rProgress: {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)",
                    end="",
                    flush=True,
                )

            file_path = await message.download_media(
                file=str(folder), progress_callback=progress_callback
            )

            print()  # New line after progress

            if file_path:
                click.echo(click.style(f"✓ Successfully downloaded to: {file_path}", fg="green"))
                await client.disconnect()
                return True
            else:
                click.echo(click.style("✗ Failed to download", fg="red"))
                await client.disconnect()
                return False

        except Exception as e:
            click.echo(click.style(f"✗ Download failed: {e}", fg="red"))
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
