"""
AutoAnimeBot - Main Entry Point
Recreated for 2025 with modern tech stack
"""

import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from config import Config
from database import Database
from scheduler import AnimeScheduler
from downloader import AnimeDownloader
from uploader import TelegramUploader
from flask import Flask
import threading
import asyncio
import logging
import os            # <--- ADD THIS
import threading     # <--- ADD THIS
from flask import Flask # <--- ADD THIS
from pyrogram import Client, filters, idle
# ... keep your other imports (Config, Database, etc.)
# Setup logging

webapp = Flask(__name__)

@webapp.route('/')
def health_check():
    return "Bot is Running!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    webapp.run(host='0.0.0.0', port=port)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot client
app = Client(
    name="AutoAnimeBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=4
)

# Initialize components
db = Database()
scheduler = AnimeScheduler(db)
downloader = AnimeDownloader()
uploader = TelegramUploader(app, db)


# ==================== Bot Commands ====================

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Welcome message"""
    welcome_text = f"""
👋 **Welcome to AutoAnimeBot!**

I automatically download and upload anime episodes to your channels.

**Available Commands:**
/status - Check bot status
/stats - View statistics
/add [anime_name] - Add anime to track
/list - List tracked anime
/remove [anime_id] - Remove anime
/logs - Get recent logs (Admin only)
/help - Show help

**Current Status:** {'🟢 Running' if scheduler.is_running else '🔴 Stopped'}
    """
    await message.reply_text(welcome_text)


@app.on_message(filters.command("status"))
async def status_command(client: Client, message: Message):
    """Show current bot status"""
    stats = await db.get_stats()
    
    status_text = f"""
📊 **Bot Status**

🟢 **System:** Running
⏰ **Uptime:** Started
📺 **Tracked Anime:** {stats.get('tracked_anime', 0)}
📥 **Total Downloads:** {stats.get('total_downloads', 0)}
📤 **Total Uploads:** {stats.get('total_uploads', 0)}
⏳ **Queue:** {stats.get('queue_size', 0)} episodes

**Last Check:** {stats.get('last_check', 'Never')}
    """
    
    await message.reply_text(status_text)


@app.on_message(filters.command("stats"))
async def stats_command(client: Client, message: Message):
    """Show detailed statistics"""
    stats = await db.get_detailed_stats()
    
    stats_text = f"""
📈 **Detailed Statistics**

**Today:**
• Downloads: {stats.get('today_downloads', 0)}
• Uploads: {stats.get('today_uploads', 0)}

**This Week:**
• Downloads: {stats.get('week_downloads', 0)}
• Uploads: {stats.get('week_uploads', 0)}

**All Time:**
• Total Episodes: {stats.get('total_episodes', 0)}
• Total Size: {stats.get('total_size', '0 GB')}
• Success Rate: {stats.get('success_rate', '0')}%
    """
    
    await message.reply_text(stats_text)


@app.on_message(filters.command("add"))
async def add_anime_command(client: Client, message: Message):
    """Add anime to tracking list"""
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: /add [anime_name]\nExample: /add Naruto Shippuden")
        return
    
    anime_name = " ".join(message.command[1:])
    msg = await message.reply_text(f"🔍 Searching for '{anime_name}'...")
    
    try:
        # Search for anime using AniList API
        results = await scheduler.search_anime(anime_name)
        
        if not results:
            await msg.edit_text("❌ No anime found with that name. Try a different spelling.")
            return
        
        # Show results (for now, just add the first match)
        anime = results[0]
        success = await db.add_anime(anime)
        
        if success:
            await msg.edit_text(
                f"✅ Added to tracking list!\n\n"
                f"**Title:** {anime['title']}\n"
                f"**Episodes:** {anime.get('episodes', 'Unknown')}\n"
                f"**Status:** {anime.get('status', 'Unknown')}"
            )
        else:
            await msg.edit_text("❌ This anime is already being tracked!")
            
    except Exception as e:
        logger.error(f"Error adding anime: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")


@app.on_message(filters.command("list"))
async def list_anime_command(client: Client, message: Message):
    """List all tracked anime"""
    anime_list = await db.get_tracked_anime()
    
    if not anime_list:
        await message.reply_text("📝 No anime being tracked yet. Use /add to add some!")
        return
    
    text = "📺 **Tracked Anime:**\n\n"
    for anime in anime_list:
        status = "🟢" if anime.get('active', True) else "🔴"
        text += f"{status} {anime['title']} (ID: {anime['id']})\n"
        text += f"   └ Latest: Episode {anime.get('latest_episode', 0)}\n\n"
    
    await message.reply_text(text)


@app.on_message(filters.command("remove"))
async def remove_anime_command(client: Client, message: Message):
    """Remove anime from tracking"""
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: /remove [anime_id]\nUse /list to see IDs")
        return
    
    try:
        anime_id = int(message.command[1])
        success = await db.remove_anime(anime_id)
        
        if success:
            await message.reply_text("✅ Anime removed from tracking list!")
        else:
            await message.reply_text("❌ Anime not found in tracking list!")
            
    except ValueError:
        await message.reply_text("❌ Invalid anime ID. Must be a number.")
    except Exception as e:
        logger.error(f"Error removing anime: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")


@app.on_message(filters.command("logs") & filters.user(Config.ADMIN_IDS))
async def logs_command(client: Client, message: Message):
    """Send recent logs (Admin only)"""
    try:
        with open('bot.log', 'rb') as log_file:
            await message.reply_document(
                document=log_file,
                file_name="bot.log",
                caption="📋 Recent bot logs"
            )
    except Exception as e:
        await message.reply_text(f"❌ Error getting logs: {str(e)}")


@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Show help information"""
    help_text = """
📚 **Help - AutoAnimeBot**

**User Commands:**
• /start - Start the bot
• /status - Check bot status
• /stats - View statistics
• /add [name] - Track new anime
• /list - Show tracked anime
• /remove [id] - Stop tracking anime
• /help - Show this message

**How it works:**
1. Add anime using /add command
2. Bot automatically checks for new episodes
3. Downloads episodes in multiple qualities
4. Uploads to your channels
5. Posts info and links

**Need more help?**
Check the documentation or contact admin.
    """
    await message.reply_text(help_text)


# ==================== Background Tasks ====================

async def check_new_episodes():
    """Background task to check for new episodes"""
    logger.info("Starting episode checker...")
    
    while True:
        try:
            logger.info("Checking for new episodes...")
            
            # Get list of tracked anime
            anime_list = await db.get_tracked_anime()
            
            for anime in anime_list:
                try:
                    # Check for new episodes
                    new_episodes = await scheduler.check_anime_updates(anime)
                    
                    if new_episodes:
                        logger.info(f"Found {len(new_episodes)} new episodes for {anime['title']}")
                        
                        for episode in new_episodes:
                            # Add to download queue
                            await db.add_to_queue(episode)
                            
                except Exception as e:
                    logger.error(f"Error checking {anime.get('title', 'Unknown')}: {e}")
                    continue
                
                # Small delay between anime checks
                await asyncio.sleep(5)
            
            # Wait 5 minutes before next check
            logger.info("Sleeping for 5 minutes...")
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Error in episode checker: {e}")
            await asyncio.sleep(60)


async def process_download_queue():
    """Background task to process download queue"""
    logger.info("Starting download processor...")
    
    while True:
        try:
            # Get next item from queue
            episode = await db.get_next_in_queue()
            
            if episode:
                logger.info(f"Processing: {episode['anime_title']} - Episode {episode['episode_number']}")
                
                # Download episode
                downloaded_files = await downloader.download_episode(episode)
                
                if downloaded_files:
                    # Upload to Telegram
                    await uploader.upload_episode(episode, downloaded_files)
                    
                    # Mark as completed
                    await db.mark_episode_completed(episode['id'])
                else:
                    # Mark as failed
                    await db.mark_episode_failed(episode['id'])
                
                # Small delay between downloads
                await asyncio.sleep(10)
            else:
                # No items in queue, wait a bit
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"Error in download processor: {e}")
            await asyncio.sleep(60)


async def update_status_message():
    """Update status message in channel periodically"""
    logger.info("Starting status updater...")
    
    while True:
        try:
            stats = await db.get_stats()
            queue = await db.get_queue_info()
            
            status_text = f"""
🤖 **AutoAnimeBot Status**

📊 **Statistics:**
• Tracked Anime: {stats.get('tracked_anime', 0)}
• Total Downloads: {stats.get('total_downloads', 0)}
• Total Uploads: {stats.get('total_uploads', 0)}

⏳ **Queue:**
• Pending: {queue.get('pending', 0)}
• Downloading: {queue.get('downloading', 0)}
• Uploading: {queue.get('uploading', 0)}

🕐 Last Updated: {asyncio.get_event_loop().time()}
            """
            
            await app.edit_message_text(
                chat_id=Config.UPLOADS_CHANNEL_ID,
                message_id=Config.STATUS_MSG_ID,
                text=status_text
            )
            
            # Update every 5 minutes
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            await asyncio.sleep(300)


# ==================== Main Entry Point ====================

async def main():
    async def main():
    """Main function"""
    logger.info("Starting AutoAnimeBot...")
    
    try:
        # --- NEW RENDER FIX LINE ---
        # This starts the web server so Render doesn't shut you down
        threading.Thread(target=run_web_server, daemon=True).start()
        
        # --- YOUR ORIGINAL LOGIC CONTINUES BELOW ---
        # Initialize database
        await db.connect()
        logger.info("Database connected")
        
        # Start the bot
        await app.start()
        logger.info("Bot started successfully!")
        
        # Start background tasks
        asyncio.create_task(check_new_episodes())
        asyncio.create_task(process_download_queue())
        asyncio.create_task(update_status_message())
        
        logger.info("All background tasks started")
        await idle()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await app.stop()
        await db.close()






# Add this at the top with other imports
from flask import Flask
import threading

# Add this before 'if __name__ == "__main__":'
webapp = Flask(__name__)

@webapp.route('/')
def health_check():
    return "Bot is running!", 200

def run_web_server():
    # Render provides the port in an environment variable
    port = int(os.environ.get("PORT", 10000))
    webapp.run(host='0.0.0.0', port=port)

# In your main() function, before 'await idle()', add:
# threading.Thread(target=run_web_server, daemon=True).start()
