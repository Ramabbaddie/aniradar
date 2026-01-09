"""
Telegram uploader - Uploads episodes to Telegram channels
Generates thumbnails and posts info to index channel
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

logger = logging.getLogger(__name__)


class TelegramUploader:
    """Handles uploading episodes to Telegram"""
    
    def __init__(self, client: Client, database):
        self.client = client
        self.db = database
        self.thumb_dir = Path("thumbnails")
        self.thumb_dir.mkdir(exist_ok=True)
    
    def generate_thumbnail(self, anime_title: str, episode_number: int, cover_image_path: Optional[Path] = None) -> Path:
        """Generate custom thumbnail for episode"""
        try:
            # Create image
            width, height = 1280, 720
            img = Image.new('RGB', (width, height), color=(20, 20, 30))
            draw = ImageDraw.Draw(img)
            
            # Add cover image if provided
            if cover_image_path and cover_image_path.exists():
                try:
                    cover = Image.open(cover_image_path)
                    cover = cover.resize((400, 600))
                    img.paste(cover, (50, 60))
                except Exception as e:
                    logger.error(f"Error adding cover image: {e}")
            
            # Add text
            try:
                # Try to use a nice font, fallback to default
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
                ep_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
                channel_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            except:
                title_font = ImageFont.load_default()
                ep_font = ImageFont.load_default()
                channel_font = ImageFont.load_default()
            
            # Draw title
            title_lines = self._wrap_text(anime_title, 30)
            y_offset = 100
            for line in title_lines[:3]:  # Max 3 lines
                draw.text((500, y_offset), line, fill=(255, 255, 255), font=title_font)
                y_offset += 70
            
            # Draw episode number
            ep_text = f"Episode {episode_number}"
            draw.text((500, height - 200), ep_text, fill=(100, 200, 255), font=ep_font)
            
            # Draw channel name
            draw.text((500, height - 100), Config.CHANNEL_TITLE, fill=(150, 150, 150), font=channel_font)
            
            # Save thumbnail
            thumb_path = self.thumb_dir / f"thumb_{anime_title.replace(' ', '_')}_E{episode_number}.jpg"
            img.save(thumb_path, "JPEG", quality=85)
            
            logger.info(f"Generated thumbnail: {thumb_path.name}")
            return thumb_path
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            # Return None to upload without thumbnail
            return None
    
    def _wrap_text(self, text: str, max_chars: int) -> List[str]:
        """Wrap text into lines"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    async def upload_to_channel(self, file_path: Path, quality: str, caption: str, thumb_path: Optional[Path] = None) -> Optional[int]:
        """Upload a single file to uploads channel"""
        try:
            logger.info(f"Uploading {quality}: {file_path.name}")
            
            message = await self.client.send_video(
                chat_id=Config.UPLOADS_CHANNEL_ID,
                video=str(file_path),
                caption=caption,
                thumb=str(thumb_path) if thumb_path else None,
                supports_streaming=True,
                progress=self._upload_progress
            )
            
            logger.info(f"Uploaded {quality}: Message ID {message.id}")
            return message.id
            
        except Exception as e:
            logger.error(f"Upload error for {quality}: {e}")
            return None
    
    async def _upload_progress(self, current: int, total: int):
        """Upload progress callback"""
        if total > 0:
            progress = (current / total) * 100
            if int(progress) % 10 == 0:  # Log every 10%
                logger.info(f"Upload progress: {progress:.1f}%")
    
    async def post_to_index_channel(self, episode_data: Dict, file_links: Dict[str, str]) -> Optional[int]:
        """Post episode info and links to index channel"""
        try:
            anime_title = episode_data["anime_title"]
            episode_number = episode_data["episode_number"]
            
            # Build caption
            caption = f"**{anime_title}**\n\n"
            caption += f"📺 Episode {episode_number}\n\n"
            caption += f"**Download Links:**\n"
            
            for quality, link in file_links.items():
                caption += f"[{quality.upper()}]({link}) | "
            
            caption = caption.rstrip(" | ")
            caption += f"\n\n💬 {Config.COMMENTS_GROUP_LINK}"
            caption += f"\n📢 {Config.INDEX_CHANNEL_USERNAME}"
            caption += f"\n\n#{anime_title.replace(' ', '')}"
            
            # Create voting buttons
            buttons = None
            if Config.ENABLE_VOTING:
                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("👍 Great", callback_data=f"vote_up_{episode_data['anime_id']}_{episode_number}"),
                        InlineKeyboardButton("👎 Bad", callback_data=f"vote_down_{episode_data['anime_id']}_{episode_number}")
                    ]
                ])
            
            # Send to index channel
            message = await self.client.send_message(
                chat_id=Config.INDEX_CHANNEL_ID,
                text=caption,
                reply_markup=buttons,
                disable_web_page_preview=False
            )
            
            logger.info(f"Posted to index channel: {anime_title} E{episode_number}")
            return message.id
            
        except Exception as e:
            logger.error(f"Error posting to index channel: {e}")
            return None
    
    async def upload_episode(self, episode_data: Dict, downloaded_files: Dict[str, Path]):
        """Upload all files for an episode"""
        try:
            anime_title = episode_data["anime_title"]
            episode_number = episode_data["episode_number"]
            
            logger.info(f"Starting upload: {anime_title} - Episode {episode_number}")
            
            # Generate thumbnail
            thumb_path = None
            if Config.ENABLE_THUMBNAILS:
                thumb_path = self.generate_thumbnail(anime_title, episode_number)
            
            # Upload each quality
            file_links = {}
            
            for quality, file_path in downloaded_files.items():
                # Build caption
                file_size = file_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                
                caption = f"**{anime_title}**\n"
                caption += f"Episode {episode_number} - {quality.upper()}\n"
                caption += f"Size: {size_mb:.1f} MB\n\n"
                caption += f"#{anime_title.replace(' ', '')}"
                
                # Upload to channel
                message_id = await self.upload_to_channel(file_path, quality, caption, thumb_path)
                
                if message_id:
                    # Create link to message
                    link = f"https://t.me/{Config.UPLOADS_CHANNEL_USERNAME}/{message_id}"
                    file_links[quality] = link
                    
                    # Increment upload counter
                    await self.db.increment_stat("total_uploads")
                
                # Sleep to avoid flood limits
                await asyncio.sleep(Config.UPLOAD_SLEEP_TIME)
            
            # Post to index channel
            if file_links:
                await self.post_to_index_channel(episode_data, file_links)
            
            # Cleanup thumbnail
            if thumb_path and thumb_path.exists():
                thumb_path.unlink()
            
            # Cleanup downloaded files if configured
            if Config.DELETE_AFTER_UPLOAD:
                for file_path in downloaded_files.values():
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Deleted: {file_path.name}")
            
            logger.info(f"Upload completed: {anime_title} E{episode_number}")
            
        except Exception as e:
            logger.error(f"Error uploading episode: {e}")
            raise
