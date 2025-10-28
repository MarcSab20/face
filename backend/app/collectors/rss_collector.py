import feedparser
import logging
from typing import List, Dict
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class RSSCollector:
    """Collecteur pour les flux RSS"""
    
    def __init__(self):
        self.sources = [
            # Sources d'actualités générales
            "http://feeds.bbci.co.uk/news/rss.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "https://www.lemonde.fr/rss/une.xml",
            "https://www.lefigaro.fr/rss/figaro_actualites.xml",
            # Sources tech
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://www.wired.com/feed/rss",
            # Blogs personnalisables
        ]
    
    def add_custom_feed(self, feed_url: str):
        """Ajouter un flux RSS personnalisé"""
        if feed_url not in self.sources:
            self.sources.append(feed_url)
    
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        Collecter les mentions d'un mot-clé dans les flux RSS
        
        Args:
            keyword: Mot-clé à rechercher
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste de mentions trouvées
        """
        mentions = []
        keyword_lower = keyword.lower()
        
        logger.info(f"Collecte RSS pour '{keyword}' sur {len(self.sources)} sources")
        
        for feed_url in self.sources:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Vérifier si le mot-clé est dans le titre ou la description
                    title = entry.get('title', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    
                    if keyword_lower in title.lower() or keyword_lower in description.lower():
                        mention = {
                            'source': 'rss',
                            'source_url': entry.get('link', ''),
                            'title': title,
                            'content': description[:1000],  # Limiter la longueur
                            'author': entry.get('author', 'Unknown'),
                            'published_at': self._parse_date(entry.get('published')),
                            'engagement_score': 0.0,
                            'metadata': {
                                'feed_title': feed.feed.get('title', ''),
                                'feed_url': feed_url,
                                'tags': [tag.term for tag in entry.get('tags', [])]
                            }
                        }
                        mentions.append(mention)
                        
                        if len(mentions) >= max_results:
                            return mentions
                            
            except Exception as e:
                logger.error(f"Erreur lors de la collecte RSS de {feed_url}: {str(e)}")
                continue
        
        logger.info(f"RSS: {len(mentions)} mentions trouvées pour '{keyword}'")
        return mentions
    
    def _parse_date(self, date_string: str) -> datetime:
        """Parser une date RSS"""
        if not date_string:
            return datetime.utcnow()
        
        try:
            # feedparser retourne déjà des tuples de temps
            from time import mktime
            if isinstance(date_string, str):
                import dateutil.parser
                return dateutil.parser.parse(date_string)
            return datetime.utcnow()
        except Exception:
            return datetime.utcnow()