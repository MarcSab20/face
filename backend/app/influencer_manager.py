"""
Système Avancé de Gestion des Influenceurs
3 catégories: Activistes Surveillés, Influenceurs Émergents, Médias Officiels
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from collections import defaultdict, Counter
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Influencer:
    """Représente un influenceur avec ses métadonnées"""
    name: str
    category: str  # 'activist', 'emerging', 'official_media'
    source: str
    total_mentions: int
    total_engagement: float
    avg_engagement: float
    sentiment_score: float  # 0-100, 100 = très positif
    reach_estimate: int
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    trending: bool
    recent_activity: List[Dict]
    keywords_mentioned: List[str]
    first_seen: datetime
    last_active: datetime


class InfluencerCategoryManager:
    """Gestionnaire des catégories d'influenceurs"""
    
    # Liste prédéfinie des activistes à surveiller
    MONITORED_ACTIVISTS = [
        "Général Valsero",
        "Michel Biem Tong",
        "Maurice Kamto",
        "Brenda Biya",
        "Patrice Nganang",
        "Brigade anti-sardinards",
        "Brigitte Amougou",
        "Cabral Libii",
        "Paul Eric Kingue"
    ]
    
    # Médias officiels et chaînes nationales
    OFFICIAL_MEDIA = [
        "CRTV",
        "Cameroon Radio Television",
        "Canal 2 International",
        "Vision 4",
        "Equinoxe TV",
        "STV",
        "LTM",
        "Cameroon Tribune",
        "Cameroon-Info.Net",
        "Journal du Cameroun"
    ]
    
    def __init__(self, db: Session):
        self.db = db
        
    def is_monitored_activist(self, author_name: str) -> bool:
        """Vérifier si un auteur est un activiste surveillé"""
        author_lower = author_name.lower()
        return any(
            activist.lower() in author_lower
            for activist in self.MONITORED_ACTIVISTS
        )
    
    def is_official_media(self, author_name: str) -> bool:
        """Vérifier si un auteur est un média officiel"""
        author_lower = author_name.lower()
        return any(
            media.lower() in author_lower
            for media in self.OFFICIAL_MEDIA
        )
    
    def classify_influencer(
        self,
        author_name: str,
        engagement_score: float,
        mentions_count: int
    ) -> str:
        """
        Classifier un influenceur dans une catégorie
        
        Returns:
            'activist', 'emerging', ou 'official_media'
        """
        # Priorité 1: Activistes surveillés
        if self.is_monitored_activist(author_name):
            return 'activist'
        
        # Priorité 2: Médias officiels
        if self.is_official_media(author_name):
            return 'official_media'
        
        # Priorité 3: Influenceurs émergents (fort engagement)
        if engagement_score > 5000 or mentions_count > 5:
            return 'emerging'
        
        return 'emerging'  # Par défaut


class AdvancedInfluencerAnalyzer:
    """Analyseur avancé d'influenceurs avec suivi et rapports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.category_manager = InfluencerCategoryManager(db)
    
    def analyze_all_influencers(
        self,
        days: int = 30,
        keyword_ids: Optional[List[int]] = None,
        min_engagement: float = 100
    ) -> Dict[str, List[Influencer]]:
        """
        Analyser tous les influenceurs et les classer par catégorie
        
        Returns:
            Dict avec 3 clés: 'activists', 'emerging', 'official_media'
        """
        from app.models import Mention, Keyword
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Query de base
        query = self.db.query(
            Mention.author,
            Mention.source,
            func.count(Mention.id).label('mention_count'),
            func.sum(Mention.engagement_score).label('total_engagement'),
            func.avg(Mention.engagement_score).label('avg_engagement'),
            func.min(Mention.published_at).label('first_seen'),
            func.max(Mention.published_at).label('last_active')
        ).filter(
            Mention.published_at >= since_date,
            Mention.author != 'Unknown',
            Mention.author != '',
            Mention.author != '[deleted]'
        )
        
        # Filtrer par keywords si spécifié
        if keyword_ids:
            query = query.filter(Mention.keyword_id.in_(keyword_ids))
        
        # Grouper et trier
        results = query.group_by(
            Mention.author,
            Mention.source
        ).having(
            func.sum(Mention.engagement_score) >= min_engagement
        ).order_by(
            desc('total_engagement')
        ).all()
        
        # Classifier les influenceurs
        categorized = {
            'activists': [],
            'emerging': [],
            'official_media': []
        }
        
        for result in results:
            author = result.author
            source = result.source
            
            # Récupérer les mentions récentes
            recent_mentions = self.db.query(Mention).filter(
                Mention.author == author,
                Mention.source == source,
                Mention.published_at >= since_date
            ).order_by(desc(Mention.engagement_score)).limit(5).all()
            
            # Analyser le sentiment
            sentiment_score = self._calculate_sentiment_score(author, source, since_date)
            
            # Estimer la portée
            reach_estimate = self._estimate_reach(result.total_engagement, source)
            
            # Évaluer le risque
            risk_level = self._assess_risk_level(
                sentiment_score,
                result.total_engagement,
                result.mention_count
            )
            
            # Détecter si trending
            trending = self._is_trending(author, source, days)
            
            # Extraire keywords mentionnés
            keywords = self._extract_keywords_mentioned(author, source, since_date)
            
            # Classifier
            category = self.category_manager.classify_influencer(
                author,
                result.total_engagement,
                result.mention_count
            )
            
            # Créer l'objet Influencer
            influencer = Influencer(
                name=author,
                category=category,
                source=source,
                total_mentions=result.mention_count,
                total_engagement=float(result.total_engagement or 0),
                avg_engagement=float(result.avg_engagement or 0),
                sentiment_score=sentiment_score,
                reach_estimate=reach_estimate,
                risk_level=risk_level,
                trending=trending,
                recent_activity=[
                    {
                        'title': m.title,
                        'url': m.source_url,
                        'engagement': m.engagement_score,
                        'date': m.published_at.isoformat() if m.published_at else None
                    }
                    for m in recent_mentions
                ],
                keywords_mentioned=keywords,
                first_seen=result.first_seen,
                last_active=result.last_active
            )
            
            # Ajouter à la bonne catégorie
            if category == 'activist':
                categorized['activists'].append(influencer)
            elif category == 'official_media':
                categorized['official_media'].append(influencer)
            else:
                categorized['emerging'].append(influencer)
        
        # Trier chaque catégorie par engagement
        for category in categorized:
            categorized[category].sort(
                key=lambda x: x.total_engagement,
                reverse=True
            )
        
        logger.info(f"✅ Influenceurs analysés: "
                   f"{len(categorized['activists'])} activistes, "
                   f"{len(categorized['emerging'])} émergents, "
                   f"{len(categorized['official_media'])} médias")
        
        return categorized
    
    def get_influencer_detailed_report(
        self,
        author_name: str,
        source: Optional[str] = None,
        days: int = 30
    ) -> Dict:
        """
        Générer un rapport détaillé sur un influenceur spécifique
        
        Args:
            author_name: Nom de l'influenceur
            source: Source (optionnel, si None analyse toutes les sources)
            days: Période d'analyse
            
        Returns:
            Rapport complet avec timeline, thèmes, engagement, etc.
        """
        from app.models import Mention, Keyword
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Query de base
        query = self.db.query(Mention).filter(
            Mention.author == author_name,
            Mention.published_at >= since_date
        )
        
        if source:
            query = query.filter(Mention.source == source)
        
        mentions = query.order_by(desc(Mention.published_at)).all()
        
        if not mentions:
            return {'error': 'Influenceur non trouvé ou inactif sur la période'}
        
        # Analyser les données
        total_engagement = sum(m.engagement_score for m in mentions)
        avg_engagement = total_engagement / len(mentions)
        
        # Timeline d'activité
        timeline = self._build_activity_timeline(mentions)
        
        # Distribution des sentiments
        sentiment_dist = {
            'positive': sum(1 for m in mentions if m.sentiment == 'positive'),
            'neutral': sum(1 for m in mentions if m.sentiment == 'neutral'),
            'negative': sum(1 for m in mentions if m.sentiment == 'negative')
        }
        
        # Thèmes abordés
        all_text = ' '.join([f"{m.title} {m.content}" for m in mentions])
        themes = self._extract_themes_from_text(all_text)
        
        # Keywords associés
        keyword_ids = set(m.keyword_id for m in mentions)
        keywords = self.db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        keywords_list = [kw.keyword for kw in keywords]
        
        # Sources d'activité
        sources_dist = Counter(m.source for m in mentions)
        
        # Contenu le plus engageant
        top_content = sorted(mentions, key=lambda m: m.engagement_score, reverse=True)[:5]
        
        # Classifier
        category = self.category_manager.classify_influencer(
            author_name,
            total_engagement,
            len(mentions)
        )
        
        # Évaluer le risque
        sentiment_score = self._calculate_sentiment_score(author_name, source, since_date)
        risk_level = self._assess_risk_level(sentiment_score, total_engagement, len(mentions))
        
        return {
            'influencer': {
                'name': author_name,
                'category': category,
                'category_label': self._get_category_label(category)
            },
            'period': {
                'days': days,
                'start_date': since_date.isoformat(),
                'end_date': datetime.utcnow().isoformat()
            },
            'activity': {
                'total_mentions': len(mentions),
                'total_engagement': total_engagement,
                'avg_engagement_per_post': avg_engagement,
                'sources': dict(sources_dist),
                'timeline': timeline
            },
            'sentiment': {
                'distribution': sentiment_dist,
                'score': sentiment_score,
                'percentages': {
                    k: round((v / len(mentions)) * 100, 1)
                    for k, v in sentiment_dist.items()
                }
            },
            'content_analysis': {
                'themes': themes,
                'keywords_associated': keywords_list,
                'top_posts': [
                    {
                        'title': m.title,
                        'url': m.source_url,
                        'engagement': m.engagement_score,
                        'sentiment': m.sentiment,
                        'date': m.published_at.isoformat() if m.published_at else None
                    }
                    for m in top_content
                ]
            },
            'risk_assessment': {
                'level': risk_level,
                'sentiment_score': sentiment_score,
                'engagement_level': 'high' if total_engagement > 10000 else ('medium' if total_engagement > 1000 else 'low'),
                'is_monitored_activist': self.category_manager.is_monitored_activist(author_name)
            }
        }
    
    def track_influencer_evolution(
        self,
        author_name: str,
        source: Optional[str] = None,
        periods: int = 4,  # Nombre de périodes à comparer
        period_days: int = 7  # Durée de chaque période
    ) -> Dict:
        """
        Suivre l'évolution d'un influenceur sur plusieurs périodes
        
        Permet de voir si un influenceur monte ou descend en influence
        """
        from app.models import Mention
        
        evolution_data = []
        
        for i in range(periods):
            # Calculer les dates de la période
            end_date = datetime.utcnow() - timedelta(days=i * period_days)
            start_date = end_date - timedelta(days=period_days)
            
            # Query pour cette période
            query = self.db.query(
                func.count(Mention.id).label('mentions'),
                func.sum(Mention.engagement_score).label('engagement')
            ).filter(
                Mention.author == author_name,
                Mention.published_at >= start_date,
                Mention.published_at < end_date
            )
            
            if source:
                query = query.filter(Mention.source == source)
            
            result = query.first()
            
            evolution_data.append({
                'period': f"Semaine -{i}",
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'mentions': result.mentions or 0,
                'engagement': float(result.engagement or 0)
            })
        
        # Inverser pour avoir chronologique
        evolution_data.reverse()
        
        # Calculer la tendance
        if len(evolution_data) >= 2:
            recent_engagement = evolution_data[-1]['engagement']
            older_engagement = evolution_data[0]['engagement']
            
            if older_engagement > 0:
                growth_rate = ((recent_engagement - older_engagement) / older_engagement) * 100
            else:
                growth_rate = 100 if recent_engagement > 0 else 0
            
            trend = 'rising' if growth_rate > 20 else ('falling' if growth_rate < -20 else 'stable')
        else:
            growth_rate = 0
            trend = 'unknown'
        
        return {
            'influencer': author_name,
            'evolution': evolution_data,
            'trend': trend,
            'growth_rate_percentage': round(growth_rate, 1),
            'analysis_period': f"{periods * period_days} jours"
        }
    
    def _calculate_sentiment_score(
        self,
        author: str,
        source: str,
        since_date: datetime
    ) -> float:
        """
        Calculer un score de sentiment 0-100
        100 = très positif, 0 = très négatif
        """
        from app.models import Mention
        
        mentions = self.db.query(Mention).filter(
            Mention.author == author,
            Mention.source == source,
            Mention.published_at >= since_date,
            Mention.sentiment != None
        ).all()
        
        if not mentions:
            return 50  # Neutre par défaut
        
        positive = sum(1 for m in mentions if m.sentiment == 'positive')
        negative = sum(1 for m in mentions if m.sentiment == 'negative')
        total = len(mentions)
        
        # Score basé sur le ratio positif vs négatif
        score = ((positive - negative) / total + 1) * 50  # Normalise 0-100
        
        return round(max(0, min(100, score)), 1)
    
    def _estimate_reach(self, total_engagement: float, source: str) -> int:
        """Estimer la portée potentielle basée sur l'engagement"""
        
        # Ratios moyens engagement/portée par plateforme
        ratios = {
            'youtube': 0.02,      # 2% engagement
            'tiktok': 0.05,       # 5% engagement
            'instagram': 0.03,
            'twitter': 0.01,
            'reddit': 0.1,
            'facebook': 0.015
        }
        
        ratio = ratios.get(source, 0.05)
        estimated_reach = int(total_engagement / ratio)
        
        return estimated_reach
    
    def _assess_risk_level(
        self,
        sentiment_score: float,
        total_engagement: float,
        mentions_count: int
    ) -> str:
        """Évaluer le niveau de risque d'un influenceur"""
        
        risk_score = 0
        
        # Facteur 1: Sentiment négatif
        if sentiment_score < 30:
            risk_score += 3
        elif sentiment_score < 50:
            risk_score += 1
        
        # Facteur 2: Engagement élevé
        if total_engagement > 50000:
            risk_score += 2
        elif total_engagement > 10000:
            risk_score += 1
        
        # Facteur 3: Activité soutenue
        if mentions_count > 20:
            risk_score += 1
        
        # Déterminer le niveau
        if risk_score >= 5:
            return 'critical'
        elif risk_score >= 3:
            return 'high'
        elif risk_score >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _is_trending(self, author: str, source: str, days: int) -> bool:
        """Déterminer si un influenceur est en tendance (croissance récente)"""
        from app.models import Mention
        
        # Comparer activité récente vs ancienne
        mid_point = datetime.utcnow() - timedelta(days=days//2)
        since_date = datetime.utcnow() - timedelta(days=days)
        
        recent_count = self.db.query(func.count(Mention.id)).filter(
            Mention.author == author,
            Mention.source == source,
            Mention.published_at >= mid_point
        ).scalar()
        
        older_count = self.db.query(func.count(Mention.id)).filter(
            Mention.author == author,
            Mention.source == source,
            Mention.published_at >= since_date,
            Mention.published_at < mid_point
        ).scalar()
        
        # Trending si croissance > 50%
        return recent_count > older_count * 1.5 if older_count > 0 else False
    
    def _extract_keywords_mentioned(
        self,
        author: str,
        source: str,
        since_date: datetime
    ) -> List[str]:
        """Extraire les keywords associés aux mentions de l'influenceur"""
        from app.models import Mention, Keyword
        
        keyword_ids = self.db.query(Mention.keyword_id).filter(
            Mention.author == author,
            Mention.source == source,
            Mention.published_at >= since_date
        ).distinct().all()
        
        keyword_ids_list = [kid[0] for kid in keyword_ids]
        
        keywords = self.db.query(Keyword).filter(
            Keyword.id.in_(keyword_ids_list)
        ).all()
        
        return [kw.keyword for kw in keywords]
    
    def _build_activity_timeline(self, mentions: List) -> List[Dict]:
        """Construire une timeline d'activité quotidienne"""
        
        # Grouper par jour
        daily_activity = defaultdict(lambda: {'count': 0, 'engagement': 0})
        
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.strftime('%Y-%m-%d')
                daily_activity[date_key]['count'] += 1
                daily_activity[date_key]['engagement'] += mention.engagement_score
        
        # Convertir en liste triée
        timeline = [
            {
                'date': date,
                'mentions': data['count'],
                'total_engagement': data['engagement']
            }
            for date, data in sorted(daily_activity.items())
        ]
        
        return timeline
    
    def _extract_themes_from_text(self, text: str) -> List[str]:
        """Extraire les thèmes principaux d'un texte"""
        from collections import Counter
        
        # Mots vides à ignorer
        stop_words = {
            'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'mais',
            'est', 'sont', 'a', 'ont', 'pour', 'dans', 'sur', 'avec', 'par', 'que',
            'qui', 'dont', 'où', 'ce', 'cette', 'ces', 'son', 'sa', 'ses', 'mon',
            'ma', 'mes', 'ton', 'ta', 'tes', 'notre', 'votre', 'leur', 'leurs',
            'the', 'and', 'or', 'is', 'are', 'of', 'to', 'in', 'for', 'with', 'on'
        }
        
        # Extraire les mots significatifs
        words = [
            w.lower() for w in text.split()
            if len(w) > 4 and w.lower() not in stop_words and w.isalpha()
        ]
        
        # Les 5 mots les plus fréquents
        common = Counter(words).most_common(5)
        themes = [word.capitalize() for word, count in common if count >= 2]
        
        return themes
    
    def _get_category_label(self, category: str) -> str:
        """Obtenir le label human-readable d'une catégorie"""
        labels = {
            'activist': 'Activiste Surveillé',
            'emerging': 'Influenceur Émergent',
            'official_media': 'Média Officiel'
        }
        return labels.get(category, category)


# Endpoint API pour les rapports d'influenceurs
def get_influencer_report_prompt(influencer_data: Dict) -> str:
    """Générer un prompt pour un rapport IA sur un influenceur"""
    
    inf = influencer_data['influencer']
    activity = influencer_data['activity']
    sentiment = influencer_data['sentiment']
    
    prompt = f"""Tu es un analyste de renseignement. Rédige un rapport sur cet influenceur.

NOM: {inf['name']}
CATÉGORIE: {inf['category_label']}
PÉRIODE: {influencer_data['period']['days']} jours

ACTIVITÉ:
- {activity['total_mentions']} publications
- Engagement total: {activity['total_engagement']:,.0f}
- Engagement moyen: {activity['avg_engagement_per_post']:,.0f}
- Sources: {', '.join(activity['sources'].keys())}

SENTIMENT:
- Positif: {sentiment['percentages']['positive']:.0f}%
- Neutre: {sentiment['percentages']['neutral']:.0f}%
- Négatif: {sentiment['percentages']['negative']:.0f}%

ÉVALUATION RISQUE:
- Niveau: {influencer_data['risk_assessment']['level'].upper()}
- Score sentiment: {influencer_data['risk_assessment']['sentiment_score']:.0f}/100

INSTRUCTIONS:
Rédige un rapport narratif en 4-5 paragraphes (PAS de listes) analysant:
1. Profil et positionnement de l'influenceur
2. Niveau d'activité et engagement
3. Tonalité des publications et risques potentiels
4. Recommandations de suivi

Style: Professionnel, factuel, adapté à un briefing sécuritaire.

RAPPORT:"""
    
    return prompt


if __name__ == '__main__':
    # Test du système
    print("✅ Système de gestion des influenceurs chargé")
    print(f"   - {len(InfluencerCategoryManager.MONITORED_ACTIVISTS)} activistes surveillés")
    print(f"   - {len(InfluencerCategoryManager.OFFICIAL_MEDIA)} médias officiels")