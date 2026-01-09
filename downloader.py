"""
Anime episode downloader
Downloads episodes in multiple qualities with retry logic
"""

import os
import logging
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional
from config import Config

logger = logging.getLogger(__name__)


class AnimeDownloader:
    """Handles downloading anime episodes"""
    
    def __init__(self):
        self.download_dir = Path(Config.DOWNLOAD_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=Config.DOWNLOAD_TIMEOUT)
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def get_file_path(self, anime_title: str, episode_number: int, quality: str) -> Path:
        """Generate file path for episode"""
        # Sanitize anime title for filename
        safe_title = "".join(c for c in anime_title if c.isalnum() or c in (' ', '-', '_'))
        safe_title = safe_title.strip().replace(' ', '_')
        
        filename = f"{safe_title}_E{episode_number:03d}_{quality}.mp4"
        return self.download_dir / filename
    
    async def download_file(self, url: str, file_path: Path, quality: str) -> bool:
        """Download a single file with progress tracking"""
        try:
            session = await self.get_session()
            
            logger.info(f"Downloading {quality}: {file_path.name}")
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Download failed with status {response.status}")
                    return False
                
                # Get file size
                total_size = int(response.headers.get('content-length', 0))
                
                # Check if file is too large
                if total_size > Config.MAX_FILE_SIZE * 1024 * 1024:
                    logger.warning(f"File too large ({total_size / 1024 / 1024:.1f} MB), skipping {quality}")
                    return False
                
                # Download file
                downloaded = 0
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress every 10MB
                        if downloaded % (10 * 1024 * 1024) == 0:
                            progress = (downloaded / total_size * 100) if total_size > 0 else 0
                            logger.info(f"Progress {quality}: {progress:.1f}%")
                
                logger.info(f"Download completed: {file_path.name} ({downloaded / 1024 / 1024:.1f} MB)")
                return True
                
        except asyncio.TimeoutError:
            logger.error(f"Download timeout for {quality}")
            # Delete partial file
            if file_path.exists():
                file_path.unlink()
            return False
            
        except Exception as e:
            logger.error(f"Download error for {quality}: {e}")
            # Delete partial file
            if file_path.exists():
                file_path.unlink()
            return False
    
    async def download_episode(self, episode_data: Dict) -> Dict[str, Path]:
        """Download episode in all available qualities"""
        anime_title = episode_data["anime_title"]
        episode_number = episode_data["episode_number"]
        download_links = episode_data.get("download_links", {})
        
        logger.info(f"Starting download: {anime_title} - Episode {episode_number}")
        
        downloaded_files = {}
        
        # Download each quality
        for quality in Config.DOWNLOAD_QUALITIES:
            # Check if link exists for this quality
            link = download_links.get(quality)
            
            if not link:
                logger.warning(f"No {quality} link available for {anime_title} E{episode_number}")
                continue
            
            file_path = self.get_file_path(anime_title, episode_number, quality)
            
            # Skip if already downloaded
            if file_path.exists():
                logger.info(f"File already exists: {file_path.name}")
                downloaded_files[quality] = file_path
                continue
            
            # Try downloading with retries
            success = False
            for attempt in range(Config.MAX_RETRIES):
                if attempt > 0:
                    logger.info(f"Retry {attempt + 1}/{Config.MAX_RETRIES} for {quality}")
                    await asyncio.sleep(5)  # Wait before retry
                
                success = await self.download_file(link, file_path, quality)
                
                if success:
                    downloaded_files[quality] = file_path
                    break
            
            if not success:
                logger.error(f"Failed to download {quality} after {Config.MAX_RETRIES} attempts")
        
        if not downloaded_files:
            logger.error(f"No files downloaded for {anime_title} E{episode_number}")
            return {}
        
        logger.info(f"Download completed: {anime_title} E{episode_number} ({len(downloaded_files)} qualities)")
        return downloaded_files
    
    def cleanup_file(self, file_path: Path):
        """Delete a downloaded file"""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path.name}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
    
    def cleanup_episode(self, downloaded_files: Dict[str, Path]):
        """Delete all files for an episode"""
        for file_path in downloaded_files.values():
            self.cleanup_file(file_path)
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        try:
            return file_path.stat().st_size
        except Exception:
            return 0
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size for display"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / 1024 / 1024:.1f} MB"
        else:
            return f"{size_bytes / 1024 / 1024 / 1024:.1f} GB"
