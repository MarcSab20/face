import logging
from typing import List, Dict
from datetime import datetime
import requests
from app.config import settings

logger = logging.getLogger(__name__)

class YouTubeCollector:
    """Collecteur pour YouTube via l'API Data v3"""
    
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        if not self.api_key:
            logger.warning("YouTube API key not configured")
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        Collecter les vidéos mentionnant un mot-clé sur YouTube
        
        Args:
            keyword: Mot-clé à rechercher
            max_results: Nombre maximum de résultats (max 50 par requête API)
            
        Returns:
            Liste de mentions trouvées
        """
        if not self.api_key:
            logger.warning("YouTube collector not initialized")
            return []
        
        mentions = []
        
        try:
            logger.info(f"Recherche YouTube pour '{keyword}'")
            
            # Recherche de vidéos
            search_url = f"{self.base_url}/search"
            params = {
                'part': 'snippet',
                'q': keyword,
                'key': self.api_key,
                'type': 'video',
                'maxResults': min(max_results, 50),
                'order': 'date',
                'relevanceLanguage': 'fr'
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            video_ids = [item['id']['videoId'] for item in data.get('items', [])]
            
            if not video_ids:
                logger.info(f"YouTube: Aucune vidéo trouvée pour '{keyword}'")
                return []
            
            # Obtenir les statistiques des vidéos
            stats_url = f"{self.base_url}/videos"
            stats_params = {
                'part': 'statistics,contentDetails',
                'id': ','.join(video_ids),
                'key': self.api_key
            }
            
            stats_response = requests.get(stats_url, params=stats_params, timeout=10)
            stats_response.raise_for_status()
            stats_data = stats_response.json()
            
            # Créer un dictionnaire des statistiques
            stats_dict = {
                item['id']: item for item in stats_data.get('items', [])
            }
            
            # Combiner les résultats
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                stats = stats_dict.get(video_id, {}).get('statistics', {})
                
                # Calculer le score d'engagement
                views = int(stats.get('viewCount', 0))
                likes = int(stats.get('likeCount', 0))
                comments = int(stats.get('commentCount', 0))
                engagement_score = views + (likes * 10) + (comments * 50)
                
                mention = {
                    'source': 'youtube',
                    'source_url': f"https://www.youtube.com/watch?v={video_id}",
                    'title': snippet.get('title', ''),
                    'content': snippet.get('description', '')[:1000],
                    'author': snippet.get('channelTitle', ''),
                    'published_at': self._parse_youtube_date(snippet.get('publishedAt')),
                    'engagement_score': float(engagement_score),
                    'metadata': {
                        'video_id': video_id,
                        'channel_id': snippet.get('channelId', ''),
                        'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                        'view_count': views,
                        'like_count': likes,
                        'comment_count': comments,
                        'duration': stats_dict.get(video_id, {}).get('contentDetails', {}).get('duration', '')
                    }
                }
                mentions.append(mention)
            
            logger.info(f"YouTube: {len(mentions)} vidéos trouvées pour '{keyword}'")
            return mentions
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la collecte YouTube: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return mentions
        except Exception as e:
            logger.error(f"Erreur inattendue YouTube: {str(e)}")
            return mentions
    
    def _parse_youtube_date(self, date_string: str) -> datetime:
        """Parser une date YouTube (format ISO 8601)"""
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except Exception:
            return datetime.utcnow()
    
    def get_channel_videos(self, channel_id: str, max_results: int = 10) -> List[Dict]:
        """Obtenir les dernières vidéos d'une chaîne spécifique"""
        if not self.api_key:
            return []
        
        try:
            search_url = f"{self.base_url}/search"
            params = {
                'part': 'snippet',
                'channelId': channel_id,
                'key': self.api_key,
                'type': 'video',
                'maxResults': max_results,
                'order': 'date'
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get('items', [])
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vidéos de la chaîne: {str(e)}")
            return []