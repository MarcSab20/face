"""
Service d'analyse des influenceurs
"""

import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.models import Mention

logger = logging.getLogger(__name__)


class InfluencerAnalyzer:
    """Analyseur des comptes influents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_top_influencers(
        self,
        days: int = 30,
        limit: int = 20,
        source: str = None
    ) -> List[Dict]:
        """
        Obtenir les top influenceurs par engagement
        
        Args:
            days: Période d'analyse en jours
            limit: Nombre d'influenceurs à retourner
            source: Filtrer par source (optionnel)
            
        Returns:
            Liste des influenceurs avec leurs statistiques
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Requête de base
        query = self.db.query(
            Mention.author,
            Mention.source,
            func.count(Mention.id).label('mention_count'),
            func.sum(Mention.engagement_score).label('total_engagement'),
            func.avg(Mention.engagement_score).label('avg_engagement'),
            func.count(func.nullif(Mention.sentiment == 'positive', False)).label('positive_count'),
            func.count(func.nullif(Mention.sentiment == 'negative', False)).label('negative_count'),
        ).filter(
            Mention.published_at >= since_date,
            Mention.author != 'Unknown',
            Mention.author != ''
        )
        
        # Filtrer par source si spécifié
        if source:
            query = query.filter(Mention.source == source)
        
        # Grouper et trier
        results = query.group_by(
            Mention.author,
            Mention.source
        ).order_by(
            desc('total_engagement')
        ).limit(limit).all()
        
        influencers = []
        for result in results:
            # Calculer le score de sentiment
            total_sentiment = result.positive_count + result.negative_count
            sentiment_score = 0
            if total_sentiment > 0:
                sentiment_score = (result.positive_count / total_sentiment) * 100
            
            # Obtenir quelques mentions récentes
            recent_mentions = self.db.query(Mention).filter(
                Mention.author == result.author,
                Mention.source == result.source,
                Mention.published_at >= since_date
            ).order_by(
                Mention.published_at.desc()
            ).limit(3).all()
            
            influencer = {
                'author': result.author,
                'source': result.source,
                'mention_count': result.mention_count,
                'total_engagement': float(result.total_engagement or 0),
                'avg_engagement': float(result.avg_engagement or 0),
                'sentiment_score': round(sentiment_score, 1),
                'positive_mentions': result.positive_count,
                'negative_mentions': result.negative_count,
                'recent_mentions': [
                    {
                        'title': m.title,
                        'url': m.source_url,
                        'engagement': m.engagement_score,
                        'sentiment': m.sentiment,
                        'published_at': m.published_at.isoformat() if m.published_at else None
                    }
                    for m in recent_mentions
                ],
                'profile_url': self._get_profile_url(result.author, result.source)
            }
            
            influencers.append(influencer)
        
        return influencers
    
    def get_influencers_by_source(self, days: int = 30) -> Dict[str, List[Dict]]:
        """
        Obtenir les top influenceurs groupés par source
        
        Args:
            days: Période d'analyse en jours
            
        Returns:
            Dictionnaire avec les influenceurs par source
        """
        sources = ['youtube', 'tiktok', 'reddit', 'twitter', 'instagram']
        
        result = {}
        for source in sources:
            influencers = self.get_top_influencers(days=days, limit=5, source=source)
            if influencers:
                result[source] = influencers
        
        return result
    
    def get_influencer_growth(self, author: str, source: str, days: int = 30) -> Dict:
        """
        Analyser la croissance d'un influenceur
        
        Args:
            author: Nom de l'auteur
            source: Source
            days: Période d'analyse
            
        Returns:
            Données de croissance
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        mid_date = datetime.utcnow() - timedelta(days=days//2)
        
        # Première moitié de période
        first_half = self.db.query(
            func.count(Mention.id).label('count'),
            func.sum(Mention.engagement_score).label('engagement')
        ).filter(
            Mention.author == author,
            Mention.source == source,
            Mention.published_at >= since_date,
            Mention.published_at < mid_date
        ).first()
        
        # Deuxième moitié
        second_half = self.db.query(
            func.count(Mention.id).label('count'),
            func.sum(Mention.engagement_score).label('engagement')
        ).filter(
            Mention.author == author,
            Mention.source == source,
            Mention.published_at >= mid_date
        ).first()
        
        # Calculer la croissance
        mention_growth = 0
        engagement_growth = 0
        
        if first_half.count and first_half.count > 0:
            mention_growth = ((second_half.count - first_half.count) / first_half.count) * 100
        
        if first_half.engagement and first_half.engagement > 0:
            engagement_growth = ((second_half.engagement - first_half.engagement) / first_half.engagement) * 100
        
        return {
            'author': author,
            'source': source,
            'period_days': days,
            'first_half': {
                'mentions': first_half.count or 0,
                'engagement': float(first_half.engagement or 0)
            },
            'second_half': {
                'mentions': second_half.count or 0,
                'engagement': float(second_half.engagement or 0)
            },
            'growth': {
                'mentions_percent': round(mention_growth, 1),
                'engagement_percent': round(engagement_growth, 1)
            }
        }
    
    def _get_profile_url(self, author: str, source: str) -> str:
        """
        Construire l'URL du profil selon la source
        
        Args:
            author: Nom de l'auteur
            source: Source
            
        Returns:
            URL du profil
        """
        author_clean = author.replace('@', '').replace(' ', '')
        
        urls = {
            'youtube': f"https://www.youtube.com/@{author_clean}",
            'tiktok': f"https://www.tiktok.com/@{author_clean}",
            'twitter': f"https://twitter.com/{author_clean}",
            'instagram': f"https://www.instagram.com/{author_clean}",
            'reddit': f"https://www.reddit.com/user/{author_clean}",
            'telegram': f"https://t.me/{author_clean}",
        }
        
        return urls.get(source, '#')