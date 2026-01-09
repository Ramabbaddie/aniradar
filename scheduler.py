"""
Anime scheduler - Checks for new episodes using AniList and Consumet APIs
"""

import logging
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)


class AnimeScheduler:
    """Handles anime scheduling and episode detection"""
    
    def __init__(self, database):
        self.db = database
        self.is_running = False
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    # ==================== AniList API Methods ====================
    
    async def search_anime(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for anime using AniList API"""
        graphql_query = """
        query ($search: String, $perPage: Int) {
            Page(page: 1, perPage: $perPage) {
                media(search: $search, type: ANIME, sort: POPULARITY_DESC) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    episodes
                    status
                    coverImage {
                        large
                        medium
                    }
                    description
                    season
                    seasonYear
                    genres
                }
            }
        }
        """
        
        variables = {
            "search": query,
            "perPage": limit
        }
        
        try:
            session = await self.get_session()
            async with session.post(
                Config.ANILIST_API,
                json={"query": graphql_query, "variables": variables}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    media_list = data.get("data", {}).get("Page", {}).get("media", [])
                    
                    results = []
                    for media in media_list:
                        results.append({
                            "id": media["id"],
                            "title": media["title"]["english"] or media["title"]["romaji"],
                            "title_english": media["title"]["english"],
                            "title_romaji": media["title"]["romaji"],
                            "episodes": media.get("episodes", 0),
                            "status": media["status"],
                            "cover_image": media["coverImage"]["large"],
                            "description": media.get("description", ""),
                            "genres": media.get("genres", [])
                        })
                    
                    return results
                else:
                    logger.error(f"AniList API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching anime: {e}")
            return []
    
    async def get_anime_info(self, anime_id: int) -> Optional[Dict]:
        """Get detailed anime information from AniList"""
        graphql_query = """
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title {
                    romaji
                    english
                    native
                }
                episodes
                status
                coverImage {
                    large
                    medium
                }
                bannerImage
                description
                season
                seasonYear
                genres
                averageScore
                nextAiringEpisode {
                    episode
                    airingAt
                }
            }
        }
        """
        
        variables = {"id": anime_id}
        
        try:
            session = await self.get_session()
            async with session.post(
                Config.ANILIST_API,
                json={"query": graphql_query, "variables": variables}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    media = data.get("data", {}).get("Media", {})
                    
                    if not media:
                        return None
                    
                    return {
                        "id": media["id"],
                        "title": media["title"]["english"] or media["title"]["romaji"],
                        "title_english": media["title"]["english"],
                        "title_romaji": media["title"]["romaji"],
                        "episodes": media.get("episodes", 0),
                        "status": media["status"],
                        "cover_image": media["coverImage"]["large"],
                        "banner_image": media.get("bannerImage"),
                        "description": media.get("description", ""),
                        "genres": media.get("genres", []),
                        "score": media.get("averageScore", 0),
                        "next_episode": media.get("nextAiringEpisode", {}).get("episode", 0),
                        "next_airing": media.get("nextAiringEpisode", {}).get("airingAt", 0)
                    }
                else:
                    logger.error(f"AniList API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting anime info: {e}")
            return None
    
    # ==================== Consumet API Methods ====================
    
    async def get_recent_episodes(self, page: int = 1) -> List[Dict]:
        """Get recent episodes from Consumet API"""
        try:
            session = await self.get_session()
            url = f"{Config.CONSUMET_API}/meta/anilist/recent-episodes"
            params = {"page": page, "perPage": 20}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
                else:
                    logger.error(f"Consumet API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting recent episodes: {e}")
            return []
    
    async def get_episode_links(self, episode_id: str) -> Dict:
        """Get download links for an episode from Consumet"""
        try:
            session = await self.get_session()
            url = f"{Config.CONSUMET_API}/meta/anilist/watch/{episode_id}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract links by quality
                    links = {}
                    for source in data.get("sources", []):
                        quality = source.get("quality", "unknown")
                        url = source.get("url", "")
                        if url:
                            links[quality] = url
                    
                    return links
                else:
                    logger.error(f"Consumet API error: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting episode links: {e}")
            return {}
    
    async def search_anime_episodes(self, anime_title: str) -> List[Dict]:
        """Search for anime episodes on Consumet"""
        try:
            session = await self.get_session()
            url = f"{Config.CONSUMET_API}/meta/anilist/{anime_title}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Get first result
                    if data.get("results"):
                        anime = data["results"][0]
                        anime_id = anime.get("id")
                        
                        # Get episodes for this anime
                        return await self.get_anime_episodes(anime_id)
                    
                    return []
                else:
                    logger.error(f"Consumet search error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching anime episodes: {e}")
            return []
    
    async def get_anime_episodes(self, anime_id: str) -> List[Dict]:
        """Get all episodes for an anime from Consumet"""
        try:
            session = await self.get_session()
            url = f"{Config.CONSUMET_API}/meta/anilist/info/{anime_id}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("episodes", [])
                else:
                    logger.error(f"Consumet API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting anime episodes: {e}")
            return []
    
    # ==================== Episode Checking Logic ====================
    
    async def check_anime_updates(self, anime: Dict) -> List[Dict]:
        """Check for new episodes for a specific anime"""
        try:
            anime_id = anime["anime_id"]
            anime_title = anime["title"]
            latest_episode = anime.get("latest_episode", 0)
            
            logger.info(f"Checking updates for {anime_title} (latest: Episode {latest_episode})")
            
            # Get anime info from AniList
            anime_info = await self.get_anime_info(anime_id)
            
            if not anime_info:
                logger.warning(f"Could not get info for anime ID {anime_id}")
                return []
            
            # Check if there's a next airing episode
            next_episode = anime_info.get("next_episode", 0)
            
            if next_episode <= latest_episode:
                logger.info(f"No new episodes for {anime_title}")
                return []
            
            # Search for episodes on Consumet
            episodes = await self.search_anime_episodes(anime_title)
            
            new_episodes = []
            for episode in episodes:
                episode_num = episode.get("number", 0)
                
                # Check if this is a new episode
                if episode_num > latest_episode:
                    # Check if already in database
                    exists = await self.db.episode_exists(anime_id, episode_num)
                    
                    if not exists:
                        episode_id = episode.get("id", "")
                        
                        # Get download links
                        links = await self.get_episode_links(episode_id)
                        
                        episode_data = {
                            "anime_id": anime_id,
                            "anime_title": anime_title,
                            "episode_number": episode_num,
                            "title": episode.get("title", f"Episode {episode_num}"),
                            "download_links": links,
                            "aired_at": datetime.utcnow()
                        }
                        
                        new_episodes.append(episode_data)
                        
                        # Add to database
                        await self.db.add_episode(episode_data)
                        
                        logger.info(f"Found new episode: {anime_title} - Episode {episode_num}")
            
            # Update anime's latest episode
            if new_episodes:
                max_episode = max(ep["episode_number"] for ep in new_episodes)
                await self.db.update_anime_episode(anime_id, max_episode)
            
            return new_episodes
            
        except Exception as e:
            logger.error(f"Error checking anime updates: {e}")
            return []
    
    async def get_airing_schedule(self) -> List[Dict]:
        """Get today's airing schedule from AniList"""
        graphql_query = """
        query ($airingAt_greater: Int, $airingAt_lesser: Int) {
            Page(page: 1, perPage: 50) {
                airingSchedules(
                    airingAt_greater: $airingAt_greater
                    airingAt_lesser: $airingAt_lesser
                    sort: TIME
                ) {
                    media {
                        id
                        title {
                            romaji
                            english
                        }
                        coverImage {
                            medium
                        }
                    }
                    episode
                    airingAt
                }
            }
        }
        """
        
        # Get current timestamp and end of day
        now = int(datetime.utcnow().timestamp())
        end_of_day = now + 86400  # 24 hours
        
        variables = {
            "airingAt_greater": now,
            "airingAt_lesser": end_of_day
        }
        
        try:
            session = await self.get_session()
            async with session.post(
                Config.ANILIST_API,
                json={"query": graphql_query, "variables": variables}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    schedules = data.get("data", {}).get("Page", {}).get("airingSchedules", [])
                    
                    results = []
                    for schedule in schedules:
                        media = schedule["media"]
                        results.append({
                            "anime_id": media["id"],
                            "title": media["title"]["english"] or media["title"]["romaji"],
                            "episode": schedule["episode"],
                            "airing_at": schedule["airingAt"],
                            "cover_image": media["coverImage"]["medium"]
                        })
                    
                    return results
                else:
                    logger.error(f"AniList API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting airing schedule: {e}")
            return []
