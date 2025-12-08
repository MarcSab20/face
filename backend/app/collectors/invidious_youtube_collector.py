"""
Collecteur YouTube via Invidious RSS
Gratuit, sans API key nécessaire
"""

import logging
import feedparser
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class InvidiousYouTubeCollector:
    """
    Collecteur YouTube via flux RSS Invidious
    
    Avantages:
    - Gratuit, pas de quota
    - Pas d'API key nécessaire
    - Simple et fiable
    """
    
    INVIDIOUS_INSTANCES = [
        "https://invidious.fdn.fr",
        "https://invidious.snopyta.org",
        "https://yewtu.be",
        "https://invidious.kavin.rocks",
        "https://vid.puffyan.us"
    ]
    
    def __init__(self, instance_url: Optional[str] = None):
        """
        Initialiser le collecteur
        
        Args:
            instance_url: URL d'une instance Invidious spécifique (optionnel)
        """
        self.instance_url = instance_url or self.INVIDIOUS_INSTANCES[0]
        logger.info(f"✅ Invidious YouTube Collector initialisé ({self.instance_url})")
    
    def collect_channel_videos(
        self,
        channel_id: str,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Collecter les vidéos récentes d'une chaîne YouTube
        
        Args:
            channel_id: ID de la chaîne YouTube (ex: UCXuqSBlHAE6Xw-yeJA0Tunw)
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste de vidéos
        """
        
        # Extraire l'ID si c'est une URL complète
        if "youtube.com" in channel_id or "youtu.be" in channel_id:
            channel_id = self._extract_channel_id(channel_id)
        
        rss_url = f"{self.instance_url}/feed/channel/{channel_id}"
        
        logger.info(f"🔍 Collecte vidéos YouTube (Invidious): {channel_id}")
        
        try:
            # Parser le flux RSS
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                logger.warning(f"Aucune vidéo trouvée pour {channel_id}")
                return []
            
            videos = []
            
            for entry in feed.entries[:max_results]:
                try:
                    # Extraire les données
                    video = {
                        'title': entry.get('title', 'Sans titre'),
                        'url': entry.get('link', ''),
                        'video_id': entry.get('yt_videoid', ''),
                        'author': entry.get('author', 'Inconnu'),
                        'channel_id': channel_id,
                        'published_at': self._parse_date(entry.get('published')),
                        'description': entry.get('summary', ''),
                        'thumbnail': entry.get('media_thumbnail', [{}])[0].get('url') if entry.get('media_thumbnail') else None,
                        'source': 'youtube_rss_invidious'
                    }
                    
                    videos.append(video)
                    
                except Exception as e:
                    logger.error(f"Erreur parsing vidéo: {e}")
                    continue
            
            logger.info(f"✅ {len(videos)} vidéos collectées")
            return videos
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte YouTube RSS: {e}")
            
            # Essayer une autre instance Invidious
            if self.instance_url == self.INVIDIOUS_INSTANCES[0]:
                logger.info("🔄 Tentative avec instance alternative...")
                self.instance_url = self.INVIDIOUS_INSTANCES[1]
                return self.collect_channel_videos(channel_id, max_results)
            
            return []
    
    def _extract_channel_id(self, url: str) -> str:
        """Extraire l'ID de chaîne depuis une URL"""
        import re
        
        # Pattern pour extraire l'ID
        patterns = [
            r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'youtube\.com/c/([a-zA-Z0-9_-]+)',
            r'youtube\.com/@([a-zA-Z0-9_-]+)',
            r'youtube\.com/user/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Si pas de match, retourner tel quel
        return url
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parser une date du flux RSS"""
        if not date_str:
            return None
        
        try:
            return date_parser.parse(date_str)
        except:
            return None
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict]:
        """
        Obtenir les informations d'une chaîne
        
        Returns:
            Informations de la chaîne ou None
        """
        rss_url = f"{self.instance_url}/feed/channel/{channel_id}"
        
        try:
            feed = feedparser.parse(rss_url)
            
            if not feed.feed:
                return None
            
            return {
                'title': feed.feed.get('title', 'Inconnu'),
                'description': feed.feed.get('subtitle', ''),
                'link': feed.feed.get('link', ''),
                'channel_id': channel_id
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération info chaîne: {e}")
            return None


def find_youtube_channel_id(search_term: str) -> Optional[str]:
    """
    Trouver l'ID d'une chaîne YouTube à partir d'un nom
    
    Utilise l'API de recherche Invidious
    """
    instance = InvidiousYouTubeCollector.INVIDIOUS_INSTANCES[0]
    
    try:
        url = f"{instance}/api/v1/search"
        params = {
            'q': search_term,
            'type': 'channel'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        
        if results and len(results) > 0:
            return results[0].get('authorId')
        
        return None
        
    except Exception as e:
        logger.error(f"Erreur recherche chaîne: {e}")
        return None


# Test
if __name__ == '__main__':
    collector = InvidiousYouTubeCollector()
    
    # Exemple: France 24 English
    channel_id = "UCQfwfsi5VrQ8yKZ-UWmAEFg"
    
    videos = collector.collect_channel_videos(channel_id, max_results=5)
    
    for video in videos:
        print(f"\n📹 {video['title']}")
        print(f"   Auteur: {video['author']}")
        print(f"   Date: {video['published_at']}")
        print(f"   URL: {video['url']}")