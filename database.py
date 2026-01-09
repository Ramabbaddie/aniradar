"""
Database handler for AutoAnimeBot
Uses MongoDB (Motor - async driver)
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database handler"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
        # Collections
        self.anime_collection = None
        self.episodes_collection = None
        self.queue_collection = None
        self.stats_collection = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(Config.MONGO_URI)
            self.db = self.client[Config.DATABASE_NAME]
            
            # Initialize collections
            self.anime_collection = self.db["anime"]
            self.episodes_collection = self.db["episodes"]
            self.queue_collection = self.db["queue"]
            self.stats_collection = self.db["stats"]
            
            # Create indexes
            await self.anime_collection.create_index("anime_id", unique=True)
            await self.episodes_collection.create_index([("anime_id", 1), ("episode_number", 1)])
            await self.queue_collection.create_index("status")
            
            logger.info("Database connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    # ==================== Anime Operations ====================
    
    async def add_anime(self, anime_data: Dict) -> bool:
        """Add anime to tracking list"""
        try:
            anime_doc = {
                "anime_id": anime_data["id"],
                "title": anime_data["title"],
                "title_english": anime_data.get("title_english", anime_data["title"]),
                "title_romaji": anime_data.get("title_romaji", anime_data["title"]),
                "total_episodes": anime_data.get("episodes", 0),
                "status": anime_data.get("status", "ONGOING"),
                "cover_image": anime_data.get("cover_image", ""),
                "latest_episode": 0,
                "active": True,
                "added_at": datetime.utcnow(),
                "last_checked": datetime.utcnow()
            }
            
            result = await self.anime_collection.insert_one(anime_doc)
            logger.info(f"Added anime: {anime_data['title']}")
            return bool(result.inserted_id)
            
        except Exception as e:
            if "duplicate key" in str(e):
                logger.warning(f"Anime already exists: {anime_data['title']}")
                return False
            logger.error(f"Error adding anime: {e}")
            return False
    
    async def remove_anime(self, anime_id: int) -> bool:
        """Remove anime from tracking list"""
        try:
            result = await self.anime_collection.delete_one({"anime_id": anime_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error removing anime: {e}")
            return False
    
    async def get_tracked_anime(self, active_only: bool = True) -> List[Dict]:
        """Get list of tracked anime"""
        try:
            query = {"active": True} if active_only else {}
            cursor = self.anime_collection.find(query)
            anime_list = await cursor.to_list(length=100)
            return anime_list
        except Exception as e:
            logger.error(f"Error getting tracked anime: {e}")
            return []
    
    async def update_anime_episode(self, anime_id: int, episode_number: int):
        """Update latest episode for anime"""
        try:
            await self.anime_collection.update_one(
                {"anime_id": anime_id},
                {
                    "$set": {
                        "latest_episode": episode_number,
                        "last_checked": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Updated anime {anime_id} to episode {episode_number}")
        except Exception as e:
            logger.error(f"Error updating anime episode: {e}")
    
    # ==================== Episode Operations ====================
    
    async def add_episode(self, episode_data: Dict) -> bool:
        """Add episode to database"""
        try:
            episode_doc = {
                "anime_id": episode_data["anime_id"],
                "anime_title": episode_data["anime_title"],
                "episode_number": episode_data["episode_number"],
                "title": episode_data.get("title", f"Episode {episode_data['episode_number']}"),
                "download_links": episode_data.get("download_links", {}),
                "aired_at": episode_data.get("aired_at"),
                "added_at": datetime.utcnow(),
                "status": "pending",  # pending, downloaded, uploaded, failed
                "uploaded_files": {},
                "retries": 0
            }
            
            result = await self.episodes_collection.insert_one(episode_doc)
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error adding episode: {e}")
            return False
    
    async def get_episode(self, anime_id: int, episode_number: int) -> Optional[Dict]:
        """Get episode data"""
        try:
            episode = await self.episodes_collection.find_one({
                "anime_id": anime_id,
                "episode_number": episode_number
            })
            return episode
        except Exception as e:
            logger.error(f"Error getting episode: {e}")
            return None
    
    async def episode_exists(self, anime_id: int, episode_number: int) -> bool:
        """Check if episode exists in database"""
        try:
            count = await self.episodes_collection.count_documents({
                "anime_id": anime_id,
                "episode_number": episode_number
            })
            return count > 0
        except Exception as e:
            logger.error(f"Error checking episode: {e}")
            return False
    
    # ==================== Queue Operations ====================
    
    async def add_to_queue(self, episode_data: Dict) -> bool:
        """Add episode to download queue"""
        try:
            queue_doc = {
                "anime_id": episode_data["anime_id"],
                "anime_title": episode_data["anime_title"],
                "episode_number": episode_data["episode_number"],
                "download_links": episode_data.get("download_links", {}),
                "status": "pending",  # pending, downloading, uploading, completed, failed
                "priority": episode_data.get("priority", 0),
                "added_at": datetime.utcnow(),
                "started_at": None,
                "completed_at": None,
                "retries": 0,
                "error_message": None
            }
            
            # Check if already in queue
            exists = await self.queue_collection.count_documents({
                "anime_id": episode_data["anime_id"],
                "episode_number": episode_data["episode_number"]
            })
            
            if exists:
                logger.warning(f"Episode already in queue: {episode_data['anime_title']} - {episode_data['episode_number']}")
                return False
            
            result = await self.queue_collection.insert_one(queue_doc)
            logger.info(f"Added to queue: {episode_data['anime_title']} - Episode {episode_data['episode_number']}")
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error adding to queue: {e}")
            return False
    
    async def get_next_in_queue(self) -> Optional[Dict]:
        """Get next episode from queue"""
        try:
            episode = await self.queue_collection.find_one_and_update(
                {"status": "pending"},
                {
                    "$set": {
                        "status": "downloading",
                        "started_at": datetime.utcnow()
                    }
                },
                sort=[("priority", -1), ("added_at", 1)]
            )
            return episode
        except Exception as e:
            logger.error(f"Error getting next in queue: {e}")
            return None
    
    async def mark_episode_completed(self, episode_id) -> bool:
        """Mark episode as completed"""
        try:
            result = await self.queue_collection.update_one(
                {"_id": episode_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking episode completed: {e}")
            return False
    
    async def mark_episode_failed(self, episode_id, error_message: str = None) -> bool:
        """Mark episode as failed"""
        try:
            result = await self.queue_collection.update_one(
                {"_id": episode_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": error_message,
                        "completed_at": datetime.utcnow()
                    },
                    "$inc": {"retries": 1}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking episode failed: {e}")
            return False
    
    async def get_queue_info(self) -> Dict:
        """Get queue statistics"""
        try:
            pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            cursor = self.queue_collection.aggregate(pipeline)
            results = await cursor.to_list(length=10)
            
            queue_info = {
                "pending": 0,
                "downloading": 0,
                "uploading": 0,
                "completed": 0,
                "failed": 0
            }
            
            for item in results:
                queue_info[item["_id"]] = item["count"]
            
            return queue_info
            
        except Exception as e:
            logger.error(f"Error getting queue info: {e}")
            return {}
    
    # ==================== Statistics Operations ====================
    
    async def increment_stat(self, stat_name: str, value: int = 1):
        """Increment a statistic"""
        try:
            await self.stats_collection.update_one(
                {"_id": "global"},
                {
                    "$inc": {stat_name: value},
                    "$set": {"last_updated": datetime.utcnow()}
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error incrementing stat: {e}")
    
    async def get_stats(self) -> Dict:
        """Get global statistics"""
        try:
            stats = await self.stats_collection.find_one({"_id": "global"})
            if not stats:
                return {
                    "tracked_anime": 0,
                    "total_downloads": 0,
                    "total_uploads": 0,
                    "queue_size": 0,
                    "last_check": "Never"
                }
            
            # Get current counts
            tracked_count = await self.anime_collection.count_documents({"active": True})
            queue_size = await self.queue_collection.count_documents({"status": "pending"})
            
            stats["tracked_anime"] = tracked_count
            stats["queue_size"] = queue_size
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    async def get_detailed_stats(self) -> Dict:
        """Get detailed statistics"""
        try:
            # Get overall stats
            stats = await self.get_stats()
            
            # Calculate additional stats
            total_episodes = await self.episodes_collection.count_documents({})
            completed = await self.queue_collection.count_documents({"status": "completed"})
            failed = await self.queue_collection.count_documents({"status": "failed"})
            
            success_rate = 0
            if total_episodes > 0:
                success_rate = (completed / total_episodes) * 100
            
            stats.update({
                "total_episodes": total_episodes,
                "today_downloads": 0,  # TODO: Implement time-based stats
                "today_uploads": 0,
                "week_downloads": 0,
                "week_uploads": 0,
                "total_size": "0 GB",  # TODO: Track file sizes
                "success_rate": f"{success_rate:.1f}"
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting detailed stats: {e}")
            return {}
