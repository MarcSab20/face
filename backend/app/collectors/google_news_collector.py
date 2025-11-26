"""
Collecteur Google News Professionnel
Utilise GNews API (gratuit) pour collecter articles d'actualité
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Représente un article de presse"""
    title: str
    description: str
    content: str
    url: str
    published_at: datetime
    source_name: str
    source_url: str
    author: Optional[str]
    image_url: Optional[str]
    engagement_score: float


class GoogleNewsCollectorEnhanced:
    """
    Collecteur Google News professionnel
    
    Utilise GNews API (gratuit: 100 requêtes/jour)
    Alternative: NewsAPI (gratuit: 100 requêtes/jour, 1 mois d'historique)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialiser le collecteur Google News
        
        Args:
            api_key: Clé API GNews ou NewsAPI
        """
        self.gnews_api_key = api_key
        
        if not api_key:
            logger.warning("Google News API key manquante")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Google News Enhanced Collector initialisé")
    
    def search_news(
        self,
        keyword: str,
        max_results: int = 50,
        language: str = 'fr',
        country: str = 'FR',
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[NewsArticle]:
        """
        Rechercher des articles d'actualité
        
        Args:
            keyword: Mot-clé de recherche
            max_results: Nombre max de résultats
            language: Langue (fr, en, etc.)
            country: Pays (FR, CM, etc.)
            from_date: Date de début
            to_date: Date de fin
            
        Returns:
            Liste d'articles
        """
        if not self.enabled:
            logger.warning("Google News collector non activé")
            return []
        
        try:
            logger.info(f"🔍 Recherche Google News: '{keyword}' (max {max_results})")
            
            # Essayer GNews d'abord
            articles = self._search_with_gnews(
                keyword, max_results, language, country, from_date, to_date
            )
            
            # Si échec, essayer NewsAPI
            if not articles:
                articles = self._search_with_newsapi(
                    keyword, max_results, language, from_date, to_date
                )
            
            logger.info(f"✅ {len(articles)} articles collectés")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche Google News: {e}")
            return []
    
    def _search_with_gnews(
        self,
        keyword: str,
        max_results: int,
        language: str,
        country: str,
        from_date: Optional[datetime],
        to_date: Optional[datetime]
    ) -> List[NewsArticle]:
        """Rechercher avec GNews API"""
        
        try:
            from gnews import GNews
            
            # Configuration GNews
            google_news = GNews(
                language=language,
                country=country,
                period=None,  # Pas de limitation de période
                max_results=max_results
            )
            
            # Recherche
            news_results = google_news.get_news(keyword)
            
            articles = []
            
            for item in news_results:
                try:
                    # GNews retourne des données limitées, on enrichit avec le contenu complet
                    article_data = google_news.get_full_article(item['url'])
                    
                    # Parser la date
                    pub_date = self._parse_date(item.get('published date'))
                    
                    # Filtrer par date si spécifié
                    if from_date and pub_date < from_date:
                        continue
                    if to_date and pub_date > to_date:
                        continue
                    
                    # Calculer engagement (basé sur le nom de la source)
                    engagement_score = self._estimate_engagement_from_source(
                        item.get('publisher', {}).get('title', '')
                    )
                    
                    article = NewsArticle(
                        title=item.get('title', ''),
                        description=item.get('description', ''),
                        content=article_data.text if article_data else item.get('description', ''),
                        url=item.get('url', ''),
                        published_at=pub_date,
                        source_name=item.get('publisher', {}).get('title', 'Unknown'),
                        source_url=item.get('publisher', {}).get('href', ''),
                        author=None,  # GNews ne fournit pas l'auteur
                        image_url=article_data.top_image if article_data else None,
                        engagement_score=engagement_score
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.debug(f"Erreur traitement article: {e}")
                    continue
            
            return articles
            
        except ImportError:
            logger.warning("GNews non installé. Installer avec: pip install gnews")
            return []
        except Exception as e:
            logger.error(f"Erreur GNews API: {e}")
            return []
    
    def _search_with_newsapi(
        self,
        keyword: str,
        max_results: int,
        language: str,
        from_date: Optional[datetime],
        to_date: Optional[datetime]
    ) -> List[NewsArticle]:
        """Rechercher avec NewsAPI (alternative)"""
        
        try:
            from newsapi import NewsApiClient
            
            # Initialiser NewsAPI
            newsapi = NewsApiClient(api_key=self.gnews_api_key)
            
            # Préparer les dates
            from_param = from_date.strftime('%Y-%m-%d') if from_date else None
            to_param = to_date.strftime('%Y-%m-%d') if to_date else None
            
            # Recherche
            response = newsapi.get_everything(
                q=keyword,
                language=language,
                from_param=from_param,
                to=to_param,
                sort_by='relevancy',
                page_size=min(max_results, 100)
            )
            
            articles = []
            
            for item in response.get('articles', []):
                try:
                    pub_date = datetime.fromisoformat(
                        item['publishedAt'].replace('Z', '+00:00')
                    )
                    
                    engagement_score = self._estimate_engagement_from_source(
                        item.get('source', {}).get('name', '')
                    )
                    
                    article = NewsArticle(
                        title=item.get('title', ''),
                        description=item.get('description', ''),
                        content=item.get('content', ''),
                        url=item.get('url', ''),
                        published_at=pub_date,
                        source_name=item.get('source', {}).get('name', 'Unknown'),
                        source_url=item.get('source', {}).get('url', ''),
                        author=item.get('author'),
                        image_url=item.get('urlToImage'),
                        engagement_score=engagement_score
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.debug(f"Erreur traitement article: {e}")
                    continue
            
            return articles
            
        except ImportError:
            logger.warning("NewsAPI non installé. Installer avec: pip install newsapi-python")
            return []
        except Exception as e:
            logger.error(f"Erreur NewsAPI: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parser une date de plusieurs formats possibles"""
        from dateutil import parser
        
        try:
            return parser.parse(date_str)
        except:
            return datetime.utcnow()
    
    def _estimate_engagement_from_source(self, source_name: str) -> float:
        """
        Estimer l'engagement basé sur la notoriété de la source
        
        Sources majeures = plus d'engagement potentiel
        """
        major_sources = [
            'bbc', 'cnn', 'reuters', 'afp', 'le monde', 'figaro',
            'france 24', 'rfi', 'jeune afrique', 'crtv', 'cameroon tribune'
        ]
        
        source_lower = source_name.lower()
        
        for major in major_sources:
            if major in source_lower:
                return 1000.0  # Score élevé pour sources majeures
        
        return 100.0  # Score standard
    
    def convert_to_mentions(
        self,
        articles: List[NewsArticle],
        keyword_id: int
    ) -> List[Dict]:
        """
        Convertir les articles en format mentions pour la base de données
        
        Args:
            articles: Liste d'articles
            keyword_id: ID du mot-clé associé
            
        Returns:
            Liste de mentions formatées
        """
        mentions = []
        
        for article in articles:
            mention = {
                'keyword_id': keyword_id,
                'source': 'google_news',
                'source_url': article.url,
                'title': article.title,
                'content': article.content[:2000] if article.content else article.description,
                'author': article.author or article.source_name,
                'engagement_score': float(article.engagement_score),
                'published_at': article.published_at,
                'metadata': {
                    'source_name': article.source_name,
                    'source_url': article.source_url,
                    'image_url': article.image_url,
                    'full_content_available': bool(article.content)
                }
            }
            mentions.append(mention)
        
        logger.info(f"✅ Converti {len(articles)} articles en mentions")
        return mentions
    
    def get_topic_news(
        self,
        topic: str,
        max_results: int = 20,
        language: str = 'fr',
        country: str = 'FR'
    ) -> List[NewsArticle]:
        """
        Récupérer les actualités d'un topic spécifique
        
        Topics: world, nation, business, technology, entertainment, sports, science, health
        """
        if not self.enabled:
            return []
        
        try:
            from gnews import GNews
            
            google_news = GNews(
                language=language,
                country=country,
                max_results=max_results
            )
            
            news_results = google_news.get_news_by_topic(topic)
            
            articles = []
            
            for item in news_results:
                try:
                    article_data = google_news.get_full_article(item['url'])
                    
                    article = NewsArticle(
                        title=item.get('title', ''),
                        description=item.get('description', ''),
                        content=article_data.text if article_data else '',
                        url=item.get('url', ''),
                        published_at=self._parse_date(item.get('published date')),
                        source_name=item.get('publisher', {}).get('title', 'Unknown'),
                        source_url=item.get('publisher', {}).get('href', ''),
                        author=None,
                        image_url=article_data.top_image if article_data else None,
                        engagement_score=self._estimate_engagement_from_source(
                            item.get('publisher', {}).get('title', '')
                        )
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.debug(f"Erreur traitement article topic: {e}")
                    continue
            
            logger.info(f"✅ {len(articles)} articles récupérés pour topic '{topic}'")
            return articles
            
        except Exception as e:
            logger.error(f"Erreur récupération topic {topic}: {e}")
            return []


def get_news_apis_comparison() -> str:
    """Comparaison des APIs de news disponibles"""
    return """
    📰 Comparaison APIs de News:
    
    1. GNews (Recommandé):
       ✅ Gratuit: 100 requêtes/jour
       ✅ Pas de carte de crédit requise
       ✅ Contenu complet des articles
       ✅ Multi-langue et multi-pays
       ❌ Limitation quotidienne stricte
       
       Installation: pip install gnews
       Inscription: https://gnews.io/
    
    2. NewsAPI:
       ✅ Gratuit: 100 requêtes/jour
       ✅ 1 mois d'historique
       ✅ Nombreuses sources
       ❌ Contenu tronqué (version gratuite)
       ❌ Carte de crédit requise
       
       Installation: pip install newsapi-python
       Inscription: https://newsapi.org/
    
    3. Bing News Search API:
       ✅ 1000 requêtes/mois gratuit
       ✅ Recherche puissante
       ❌ Compte Azure requis
       
       Inscription: Azure Portal
    
    4. MediaStack:
       ✅ 500 requêtes/mois gratuit
       ✅ Historique complet
       ❌ Fonctionnalités limitées (gratuit)
       
       Inscription: https://mediastack.com/
    
    Recommandation: Commencer avec GNews, compléter avec NewsAPI si besoin
    """


def get_gnews_setup_instructions() -> str:
    """Instructions pour configurer GNews"""
    return """
    📰 Configuration GNews API:
    
    1. S'inscrire sur https://gnews.io/
       - Email de confirmation
       - Clé API gratuite instantanée
    
    2. Ajouter au .env:
       GNEWS_API_KEY=votre_cle_gnews
    
    3. Limites gratuites:
       - 100 requêtes/jour
       - Pas de carte de crédit
       - Accès complet aux articles
       - Multi-langue
    
    4. Upgrade optionnel:
       - Basic ($9/mois): 1000 req/jour
       - Pro ($49/mois): 10000 req/jour
    """


if __name__ == '__main__':
    # Test du collecteur
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('GNEWS_API_KEY')
    
    if not api_key:
        print("❌ GNEWS_API_KEY non configurée")
        print(get_gnews_setup_instructions())
        print("\n" + get_news_apis_comparison())
        exit(1)
    
    collector = GoogleNewsCollectorEnhanced(api_key=api_key)
    
    print("\n🔍 Test recherche Google News...")
    articles = collector.search_news('Cameroun', max_results=5, language='fr')
    
    for article in articles:
        print(f"\n📰 {article.title}")
        print(f"   Source: {article.source_name}")
        print(f"   Date: {article.published_at}")
        print(f"   URL: {article.url}")