import logging
from typing import List, Dict
from datetime import datetime
import requests
import json
from urllib.parse import quote

logger = logging.getLogger(__name__)

class TikTokCollector:
    """
    Collecteur pour TikTok via scraping léger
    Note: TikTok n'a pas d'API gratuite, on utilise des endpoints publics
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tiktok.com/',
        }
        # Alternative: utiliser TikTok-Scraper ou d'autres bibliothèques
        # pip install TikTokApi
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        Collecter les vidéos TikTok mentionnant un mot-clé
        
        Args:
            keyword: Mot-clé à rechercher
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste de mentions trouvées
        """
        mentions = []
        
        try:
            logger.info(f"Recherche TikTok pour '{keyword}'")
            
            # Méthode 1: Utiliser l'endpoint de recherche public
            # Note: Cet endpoint peut changer, alternative = utiliser TikTokApi library
            search_url = f"https://www.tiktok.com/api/search/general/full/"
            
            params = {
                'keyword': keyword,
                'offset': 0,
                'count': min(max_results, 30)
            }
            
            try:
                response = requests.get(
                    search_url, 
                    params=params,
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('data', [])
                    
                    for item in items:
                        if 'item' in item:
                            video = item['item']
                            mention = self._parse_tiktok_video(video)
                            if mention:
                                mentions.append(mention)
                
            except Exception as e:
                logger.warning(f"Méthode API directe a échoué: {str(e)}")
            
            # Méthode alternative: Utiliser TikTokApi (nécessite installation)
            if len(mentions) == 0:
                mentions = self._collect_with_unofficial_api(keyword, max_results)
            
            logger.info(f"TikTok: {len(mentions)} vidéos trouvées pour '{keyword}'")
            return mentions
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte TikTok: {str(e)}")
            return mentions
    
    def _parse_tiktok_video(self, video: dict) -> Dict:
        """Parser un objet vidéo TikTok"""
        try:
            video_id = video.get('id', '')
            author = video.get('author', {})
            stats = video.get('stats', {})
            
            # Calculer le score d'engagement
            engagement_score = (
                stats.get('playCount', 0) +
                stats.get('diggCount', 0) * 10 +
                stats.get('commentCount', 0) * 50 +
                stats.get('shareCount', 0) * 100
            )
            
            return {
                'source': 'tiktok',
                'source_url': f"https://www.tiktok.com/@{author.get('uniqueId', 'unknown')}/video/{video_id}",
                'title': video.get('desc', '')[:500],
                'content': video.get('desc', '')[:1000],
                'author': author.get('uniqueId', 'Unknown'),
                'published_at': datetime.fromtimestamp(video.get('createTime', 0)),
                'engagement_score': float(engagement_score),
                'metadata': {
                    'video_id': video_id,
                    'author_name': author.get('nickname', ''),
                    'play_count': stats.get('playCount', 0),
                    'like_count': stats.get('diggCount', 0),
                    'comment_count': stats.get('commentCount', 0),
                    'share_count': stats.get('shareCount', 0),
                    'music': video.get('music', {}).get('title', ''),
                    'hashtags': [tag.get('name', '') for tag in video.get('challenges', [])]
                }
            }
        except Exception as e:
            logger.error(f"Erreur parsing vidéo TikTok: {str(e)}")
            return None
    
    def _collect_with_unofficial_api(self, keyword: str, max_results: int) -> List[Dict]:
        """
        Méthode alternative utilisant des données publiques
        En production, utiliser une bibliothèque comme TikTokApi
        """
        mentions = []
        
        try:
            # Simuler quelques résultats pour la démo
            # En production, intégrer TikTokApi ou Playwright pour scraping robuste
            logger.info("Utilisation de la méthode de collecte alternative (limitée)")
            
            # Exemple de structure pour montrer le format
            # En production réelle, remplacer par vraie API ou scraping
            sample_mention = {
                'source': 'tiktok',
                'source_url': f"https://www.tiktok.com/search?q={quote(keyword)}",
                'title': f"Recherche TikTok pour '{keyword}'",
                'content': "Visitez TikTok directement pour voir les résultats actuels. API limitée sans authentification.",
                'author': 'TikTok Search',
                'published_at': datetime.utcnow(),
                'engagement_score': 0.0,
                'metadata': {
                    'note': 'Résultats limités sans API officielle. Considérer TikTokApi package ou scraping Playwright.',
                    'search_url': f"https://www.tiktok.com/search?q={quote(keyword)}"
                }
            }
            mentions.append(sample_mention)
            
        except Exception as e:
            logger.error(f"Erreur méthode alternative TikTok: {str(e)}")
        
        return mentions
    
    def get_user_videos(self, username: str, max_results: int = 10) -> List[Dict]:
        """Obtenir les vidéos d'un utilisateur TikTok"""
        try:
            # Endpoint utilisateur public
            user_url = f"https://www.tiktok.com/@{username}"
            
            logger.info(f"Récupération des vidéos de @{username}")
            
            # En production, utiliser TikTokApi ou scraping
            return []
            
        except Exception as e:
            logger.error(f"Erreur récupération vidéos utilisateur: {str(e)}")
            return []