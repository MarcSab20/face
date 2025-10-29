from mastodon import Mastodon
import logging
from typing import List, Dict
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class MastodonCollector:
    """Collecteur pour Mastodon (réseau social décentralisé)"""
    
    def __init__(self):
        self.instance_url = settings.MASTODON_INSTANCE_URL or 'https://mastodon.social'
        
        try:
            self.mastodon = Mastodon(api_base_url=self.instance_url)
            logger.info(f"Mastodon API initialized ({self.instance_url})")
            self.enabled = True
        except Exception as e:
            logger.error(f"Mastodon error: {str(e)}")
            self.mastodon = None
            self.enabled = False
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """Collecter les toots mentionnant un mot-clé"""
        if not self.mastodon:
            return []
        
        mentions = []
        
        try:
            logger.info(f"Recherche Mastodon pour '{keyword}'")
            
            results = self.mastodon.search_v2(keyword, result_type='statuses')
            statuses = results.get('statuses', [])[:max_results]
            
            for status in statuses:
                account = status.get('account', {})
                
                engagement_score = (
                    status.get('reblogs_count', 0) * 10 +
                    status.get('replies_count', 0) * 5 +
                    status.get('favourites_count', 0) * 2
                )
                
                # Nettoyer le HTML
                from bs4 import BeautifulSoup
                content = BeautifulSoup(status.get('content', ''), 'html.parser').get_text()
                
                mention = {
                    'source': 'mastodon',
                    'source_url': status.get('url', ''),
                    'title': f"Toot de @{account.get('username', 'unknown')}",
                    'content': content[:1000],
                    'author': f"@{account.get('username', 'Unknown')}",
                    'published_at': datetime.fromisoformat(status.get('created_at', '').replace('Z', '+00:00')),
                    'engagement_score': float(engagement_score),
                    'metadata': {
                        'status_id': status.get('id'),
                        'reblogs': status.get('reblogs_count', 0),
                        'replies': status.get('replies_count', 0),
                        'favourites': status.get('favourites_count', 0),
                        'instance': self.instance_url,
                    }
                }
                mentions.append(mention)
            
            logger.info(f"Mastodon: {len(mentions)} toots trouvés")
            return mentions
            
        except Exception as e:
            logger.error(f"Erreur Mastodon: {str(e)}")
            return mentions