"""
Collecteur RSS Simple
"""

import logging
import feedparser
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class RSSCollector:
    """Collecteur RSS de base"""
    
    def __init__(self):
        self.enabled = True
        logger.info("RSS Collector initialisé")
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        Collecter depuis des flux RSS
        
        Args:
            keyword: Mot-clé à rechercher
            max_results: Nombre max de résultats
            
        Returns:
            Liste de mentions
        """
        logger.info(f"🔍 Collecte RSS: {keyword}")
        
        # Liste de flux RSS par défaut
        rss_feeds = [
            'https://news.google.com/rss/search?q={}&hl=fr&gl=CM&ceid=CM:fr',
            'https://www.lemonde.fr/rss/une.xml',
            'https://www.france24.com/fr/rss',
        ]
        
        mentions = []
        
        for feed_url in rss_feeds:
            try:
                url = feed_url.format(keyword) if '{}' in feed_url else feed_url
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:max_results]:
                    # Filtrer par mot-clé
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    
                    if keyword.lower() not in f"{title} {summary}".lower():
                        continue
                    
                    mention = {
                        'source': 'rss',
                        'source_url': entry.get('link', ''),
                        'title': title,
                        'content': summary[:1000],
                        'author': entry.get('author', 'RSS Feed'),
                        'engagement_score': 10.0,
                        'published_at': self._parse_date(entry.get('published')),
                        'metadata': {
                            'feed_title': feed.feed.get('title', 'Unknown Feed')
                        }
                    }
                    
                    mentions.append(mention)
                    
            except Exception as e:
                logger.error(f"Erreur collecte RSS {feed_url}: {e}")
                continue
        
        logger.info(f"✅ RSS: {len(mentions)} mentions collectées")
        return mentions[:max_results]
    
    def _parse_date(self, date_str):
        """Parser une date RSS"""
        if not date_str:
            return datetime.utcnow()
        
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return datetime.utcnow()