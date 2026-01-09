"""
Configuration file for AutoAnimeBot
All settings and environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Bot configuration class"""
    
    # ==================== Telegram Configuration ====================
    
    # Get these from https://my.telegram.org
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    
    # Get from @BotFather on Telegram
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # Your Telegram User ID (for admin commands)
    # Get it from @userinfobot
    ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",")]
    
    # ==================== Channel Configuration ====================
    
    # Index Channel - Where anime info and links will be posted
    # Format: -1001234567890 (include the -100 prefix)
    INDEX_CHANNEL_ID = int(os.environ.get("INDEX_CHANNEL_ID", "0"))
    INDEX_CHANNEL_USERNAME = os.environ.get("INDEX_CHANNEL_USERNAME", "")
    
    # Uploads Channel - Where actual video files will be uploaded
    UPLOADS_CHANNEL_ID = int(os.environ.get("UPLOADS_CHANNEL_ID", "0"))
    UPLOADS_CHANNEL_USERNAME = os.environ.get("UPLOADS_CHANNEL_USERNAME", "")
    
    # Channel Title (appears on thumbnails)
    CHANNEL_TITLE = os.environ.get("CHANNEL_TITLE", "AutoAnimeBot")
    
    # Comments Group Link (linked to index channel)
    COMMENTS_GROUP_LINK = os.environ.get("COMMENTS_GROUP_LINK", "")
    
    # Status Message ID (in uploads channel)
    # Create a message in your uploads channel and get its ID
    STATUS_MSG_ID = int(os.environ.get("STATUS_MSG_ID", "0"))
    
    # Schedule Message ID (in uploads channel)
    SCHEDULE_MSG_ID = int(os.environ.get("SCHEDULE_MSG_ID", "0"))
    
    # ==================== Database Configuration ====================
    
    # MongoDB URI - Get free database from https://cloud.mongodb.com
    MONGO_URI = os.environ.get("MONGO_URI", "")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "autoanimebot")
    
    # ==================== API Configuration ====================
    
    # Consumet API - Self-hosted or use public instance
    # Deploy your own: https://github.com/consumet/api.consumet.org
    CONSUMET_API = os.environ.get("CONSUMET_API", "https://api.consumet.org")
    
    # AniList API (no key needed)
    ANILIST_API = "https://graphql.anilist.co"
    
    # ==================== Download Configuration ====================
    
    # Download directory
    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "./downloads")
    
    # Qualities to download (360p, 480p, 720p, 1080p)
    DOWNLOAD_QUALITIES = os.environ.get("DOWNLOAD_QUALITIES", "360p,480p,720p,1080p").split(",")
    
    # Maximum file size (in MB) - Telegram limit is 2000MB for bots
    MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", "2000"))
    
    # Download timeout (in seconds) - Cancel download after this time
    DOWNLOAD_TIMEOUT = int(os.environ.get("DOWNLOAD_TIMEOUT", "3600"))  # 1 hour
    
    # Sleep time between uploads (in seconds) - To avoid flood limits
    UPLOAD_SLEEP_TIME = int(os.environ.get("UPLOAD_SLEEP_TIME", "5"))
    
    # Maximum retries for failed downloads
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
    
    # ==================== Scheduler Configuration ====================
    
    # Check interval (in seconds)
    CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "300"))  # 5 minutes
    
    # Update status interval (in seconds)
    STATUS_UPDATE_INTERVAL = int(os.environ.get("STATUS_UPDATE_INTERVAL", "300"))  # 5 minutes
    
    # ==================== Advanced Settings ====================
    
    # Enable thumbnail generation
    ENABLE_THUMBNAILS = os.environ.get("ENABLE_THUMBNAILS", "True").lower() == "true"
    
    # Enable auto episode detection
    AUTO_DETECT = os.environ.get("AUTO_DETECT", "True").lower() == "true"
    
    # Enable voting buttons on index channel
    ENABLE_VOTING = os.environ.get("ENABLE_VOTING", "True").lower() == "true"
    
    # Delete files after upload
    DELETE_AFTER_UPLOAD = os.environ.get("DELETE_AFTER_UPLOAD", "True").lower() == "true"
    
    # Log level (DEBUG, INFO, WARNING, ERROR)
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    
    # ==================== Validation ====================
    
    @classmethod
    def validate(cls):
        """Validate that all required settings are configured"""
        errors = []
        
        if cls.API_ID == 0:
            errors.append("API_ID is not set")
        
        if not cls.API_HASH:
            errors.append("API_HASH is not set")
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is not set")
        
        if not cls.MONGO_URI:
            errors.append("MONGO_URI is not set")
        
        if cls.INDEX_CHANNEL_ID == 0:
            errors.append("INDEX_CHANNEL_ID is not set")
        
        if cls.UPLOADS_CHANNEL_ID == 0:
            errors.append("UPLOADS_CHANNEL_ID is not set")
        
        if cls.STATUS_MSG_ID == 0:
            errors.append("STATUS_MSG_ID is not set (create a message in uploads channel first)")
        
        if errors:
            error_message = "Configuration errors:\n" + "\n".join(f"• {e}" for e in errors)
            raise ValueError(error_message)
        
        return True
    
    @classmethod
    def display_config(cls):
        """Display current configuration (hide sensitive data)"""
        print("\n" + "="*50)
        print("AutoAnimeBot Configuration")
        print("="*50)
        print(f"API_ID: {cls.API_ID}")
        print(f"API_HASH: {'*' * 10}")
        print(f"BOT_TOKEN: {'*' * 10}")
        print(f"Index Channel: {cls.INDEX_CHANNEL_ID}")
        print(f"Uploads Channel: {cls.UPLOADS_CHANNEL_ID}")
        print(f"Channel Title: {cls.CHANNEL_TITLE}")
        print(f"Download Qualities: {', '.join(cls.DOWNLOAD_QUALITIES)}")
        print(f"Max File Size: {cls.MAX_FILE_SIZE} MB")
        print(f"Check Interval: {cls.CHECK_INTERVAL} seconds")
        print(f"Thumbnails: {'Enabled' if cls.ENABLE_THUMBNAILS else 'Disabled'}")
        print(f"Auto Detect: {'Enabled' if cls.AUTO_DETECT else 'Disabled'}")
        print("="*50 + "\n")


# Validate configuration on import
if __name__ != "__main__":
    try:
        Config.validate()
        print("✅ Configuration validated successfully!")
    except ValueError as e:
        print(f"❌ Configuration Error:\n{e}")
        print("\n💡 Please check your .env file and set all required variables.")
        exit(1)
