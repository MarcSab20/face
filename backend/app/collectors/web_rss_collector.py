"""
Collecteur de sites web via RSS
Surveillance de journaux, blogs, sites d'actualités
"""

import logging
import feedparser
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class WebRSSCollector:
    """
    Collecteur RSS pour sites web d'actualités
    """
    
    # Liste de flux RSS populaires
    POPULAR_FEEDS = {
        'journal_du_cameroun': 'https://www.journalducameroun.com/feed/',
        'france24_afrique': 'https://www.france24.com/fr/afrique/rss',
        'rfi_afrique': 'https://www.rfi.fr/fr/afrique/rss',
        'bbc_afrique': 'https://feeds.bbci.co.uk/afrique/rss.xml',
        'cameroon_tribune': 'https://www.cameroon-tribune.cm/index.php?format=feed&type=rss',
        'afrik_com': 'https://www.afrik.com/spip.php?page=backend',
        'jeune_afrique': 'https://www.jeuneafrique.com/feed/',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BrandMonitor/2.0 (RSS Reader)'
        })
        logger.info("✅ Web RSS Collector initialisé")
    
    def collect_feed(
        self,
        feed_url: str,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Collecter les articles d'un flux RSS
        
        Args:
            feed_url: URL du flux RSS
            max_results: Nombre maximum d'articles
            
        Returns:
            Liste d'articles
        """
        logger.info(f"🔍 Collecte RSS: {feed_url}")
        
        try:
            # Parser le flux RSS
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                logger.warning(f"Aucun article trouvé: {feed_url}")
                return []
            
            articles = []
            
            for entry in feed.entries[:max_results]:
                try:
                    # Extraire les données
                    article = {
                        'title': entry.get('title', 'Sans titre'),
                        'url': entry.get('link', ''),
                        'content': self._extract_content(entry),
                        'author': entry.get('author', 'Rédaction'),
                        'published_at': self._parse_date(entry),
                        'summary': entry.get('summary', ''),
                        'categories': [tag.get('term', '') for tag in entry.get('tags', [])],
                        'feed_title': feed.feed.get('title', ''),
                        'feed_url': feed_url,
                        'source': 'web_rss'
                    }
                    
                    # Ajouter image si disponible
                    if 'media_content' in entry and entry.media_content:
                        article['image_url'] = entry.media_content[0].get('url')
                    elif 'media_thumbnail' in entry and entry.media_thumbnail:
                        article['image_url'] = entry.media_thumbnail[0].get('url')
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Erreur parsing article: {e}")
                    continue
            
            logger.info(f"✅ {len(articles)} articles collectés")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte RSS: {e}")
            return []
    
    def collect_multiple_feeds(
        self,
        feed_urls: List[str],
        max_results_per_feed: int = 20
    ) -> Dict[str, List[Dict]]:
        """
        Collecter plusieurs flux RSS en parallèle
        
        Returns:
            Dict avec feed_url comme clé et articles comme valeur
        """
        results = {}
        
        for feed_url in feed_urls:
            articles = self.collect_feed(feed_url, max_results_per_feed)
            results[feed_url] = articles
        
        total = sum(len(articles) for articles in results.values())
        logger.info(f"✅ Total: {total} articles de {len(feed_urls)} sources")
        
        return results
    
    def _extract_content(self, entry) -> str:
        """Extraire le contenu d'un article"""
        # Essayer plusieurs champs
        if 'content' in entry and entry.content:
            return entry.content[0].get('value', '')
        elif 'summary' in entry:
            return entry.get('summary', '')
        elif 'description' in entry:
            return entry.get('description', '')
        return ''
    
    def _parse_date(self, entry) -> Optional[datetime]:
        """Parser la date de publication"""
        date_fields = ['published', 'updated', 'created']
        
        for field in date_fields:
            if field in entry:
                try:
                    return date_parser.parse(entry[field])
                except:
                    continue
        
        return None
    
    def discover_feed_url(self, website_url: str) -> Optional[str]:
        """
        Découvrir automatiquement l'URL du flux RSS d'un site
        
        Args:
            website_url: URL du site web
            
        Returns:
            URL du flux RSS ou None
        """
        logger.info(f"🔍 Recherche flux RSS: {website_url}")
        
        try:
            response = self.session.get(website_url, timeout=10)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher les liens RSS dans le HTML
            rss_links = soup.find_all('link', type=['application/rss+xml', 'application/atom+xml'])
            
            if rss_links:
                feed_url = rss_links[0].get('href')
                
                # Construire URL complète si relative
                if feed_url and not feed_url.startswith('http'):
                    from urllib.parse import urljoin
                    feed_url = urljoin(website_url, feed_url)
                
                logger.info(f"✅ Flux RSS trouvé: {feed_url}")
                return feed_url
            
            # Essayer des URLs communes
            common_paths = ['/feed/', '/rss/', '/feed.xml', '/rss.xml', '/atom.xml']
            from urllib.parse import urljoin
            
            for path in common_paths:
                test_url = urljoin(website_url, path)
                try:
                    feed = feedparser.parse(test_url)
                    if feed.entries:
                        logger.info(f"✅ Flux RSS trouvé: {test_url}")
                        return test_url
                except:
                    continue
            
            logger.warning(f"Aucun flux RSS trouvé pour {website_url}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur découverte RSS: {e}")
            return None
    
    def get_popular_feeds(self) -> Dict[str, str]:
        """Obtenir les flux RSS populaires pré-configurés"""
        return self.POPULAR_FEEDS.copy()


# Test
if __name__ == '__main__':
    collector = WebRSSCollector()
    
    # Test avec France 24 Afrique
    articles = collector.collect_feed(
        'https://www.france24.com/fr/afrique/rss',
        max_results=5
    )
    
    for article in articles:
        print(f"\n📰 {article['title']}")
        print(f"   Auteur: {article['author']}")
        print(f"   Date: {article['published_at']}")
        print(f"   URL: {article['url']}")