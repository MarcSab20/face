import logging
from typing import List, Dict
from datetime import datetime
import requests
from app.config import settings

logger = logging.getLogger(__name__)

class GoogleSearchCollector:
    """Collecteur pour Google Custom Search API"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.search_engine_id = settings.GOOGLE_SEARCH_ENGINE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Custom Search API not configured")
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        Collecter les mentions d'un mot-clé via Google Custom Search
        
        Args:
            keyword: Mot-clé à rechercher
            max_results: Nombre maximum de résultats (limité à 100 par jour gratuit)
            
        Returns:
            Liste de mentions trouvées
        """
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Search collector not initialized")
            return []
        
        mentions = []
        
        try:
            logger.info(f"Recherche Google pour '{keyword}'")
            
            # Google Custom Search retourne 10 résultats max par requête
            # Limite gratuite: 100 requêtes/jour
            num_pages = min((max_results // 10) + 1, 10)  # Max 10 pages = 100 résultats
            
            for page in range(num_pages):
                start_index = page * 10 + 1
                
                params = {
                    'key': self.api_key,
                    'cx': self.search_engine_id,
                    'q': keyword,
                    'start': start_index,
                    'num': 10,
                    'dateRestrict': 'm1'  # Derniers 1 mois
                }
                
                try:
                    response = requests.get(self.base_url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    items = data.get('items', [])
                    if not items:
                        break
                    
                    for item in items:
                        mention = {
                            'source': 'google_search',
                            'source_url': item.get('link', ''),
                            'title': item.get('title', ''),
                            'content': item.get('snippet', '')[:1000],
                            'author': self._extract_domain(item.get('link', '')),
                            'published_at': self._parse_date(item.get('pagemap', {})),
                            'engagement_score': 0.0,
                            'metadata': {
                                'display_link': item.get('displayLink', ''),
                                'formatted_url': item.get('formattedUrl', ''),
                                'has_image': 'cse_image' in item.get('pagemap', {}),
                                'file_format': item.get('fileFormat', 'html'),
                                'page_map': item.get('pagemap', {})
                            }
                        }
                        mentions.append(mention)
                        
                        if len(mentions) >= max_results:
                            logger.info(f"Google Search: {len(mentions)} résultats pour '{keyword}'")
                            return mentions
                    
                    # Vérifier s'il y a plus de résultats
                    if not data.get('queries', {}).get('nextPage'):
                        break
                        
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        logger.warning("Limite de quota Google API atteinte")
                        break
                    else:
                        logger.error(f"Erreur HTTP Google Search: {str(e)}")
                        break
                        
            logger.info(f"Google Search: {len(mentions)} résultats pour '{keyword}'")
            return mentions
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte Google Search: {str(e)}")
            return mentions
    
    def _extract_domain(self, url: str) -> str:
        """Extraire le domaine d'une URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or 'Unknown'
        except Exception:
            return 'Unknown'
    
    def _parse_date(self, pagemap: dict) -> datetime:
        """Essayer d'extraire une date depuis les métadonnées"""
        try:
            # Chercher dans différents champs possibles
            metatags = pagemap.get('metatags', [{}])[0]
            
            date_fields = [
                'article:published_time',
                'datePublished',
                'publishedDate',
                'og:article:published_time',
                'date'
            ]
            
            for field in date_fields:
                date_str = metatags.get(field)
                if date_str:
                    import dateutil.parser
                    return dateutil.parser.parse(date_str)
                    
        except Exception:
            pass
        
        return datetime.utcnow()
    
    def search_news(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """Recherche spécifique dans les actualités"""
        if not self.api_key or not self.search_engine_id:
            return []
        
        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': keyword,
                'num': max_results,
                'dateRestrict': 'w1',  # Dernière semaine
                'sort': 'date'  # Trier par date
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get('items', [])
            
        except Exception as e:
            logger.error(f"Erreur recherche actualités: {str(e)}")
            return []
    
    def get_quota_usage(self) -> Dict:
        """Obtenir des informations sur l'utilisation du quota"""
        # Google Custom Search: 100 requêtes/jour gratuit
        return {
            'daily_limit': 100,
            'note': 'Vérifier la console Google Cloud pour l\'usage actuel'
        }