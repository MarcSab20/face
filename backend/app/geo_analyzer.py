"""
Service de géolocalisation et analyse géographique
"""

import logging
import re
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import Counter

from app.models import Mention

logger = logging.getLogger(__name__)


class GeoAnalyzer:
    """Analyseur géographique des mentions"""
    
    # Mapping des pays avec codes ISO et coordonnées
    COUNTRY_DATA = {
        'france': {'code': 'FR', 'lat': 46.2276, 'lon': 2.2137, 'name': 'France'},
        'états-unis': {'code': 'US', 'lat': 37.0902, 'lon': -95.7129, 'name': 'États-Unis'},
        'usa': {'code': 'US', 'lat': 37.0902, 'lon': -95.7129, 'name': 'États-Unis'},
        'united states': {'code': 'US', 'lat': 37.0902, 'lon': -95.7129, 'name': 'États-Unis'},
        'royaume-uni': {'code': 'GB', 'lat': 55.3781, 'lon': -3.4360, 'name': 'Royaume-Uni'},
        'uk': {'code': 'GB', 'lat': 55.3781, 'lon': -3.4360, 'name': 'Royaume-Uni'},
        'allemagne': {'code': 'DE', 'lat': 51.1657, 'lon': 10.4515, 'name': 'Allemagne'},
        'germany': {'code': 'DE', 'lat': 51.1657, 'lon': 10.4515, 'name': 'Allemagne'},
        'espagne': {'code': 'ES', 'lat': 40.4637, 'lon': -3.7492, 'name': 'Espagne'},
        'spain': {'code': 'ES', 'lat': 40.4637, 'lon': -3.7492, 'name': 'Espagne'},
        'italie': {'code': 'IT', 'lat': 41.8719, 'lon': 12.5674, 'name': 'Italie'},
        'italy': {'code': 'IT', 'lat': 41.8719, 'lon': 12.5674, 'name': 'Italie'},
        'canada': {'code': 'CA', 'lat': 56.1304, 'lon': -106.3468, 'name': 'Canada'},
        'japon': {'code': 'JP', 'lat': 36.2048, 'lon': 138.2529, 'name': 'Japon'},
        'japan': {'code': 'JP', 'lat': 36.2048, 'lon': 138.2529, 'name': 'Japon'},
        'chine': {'code': 'CN', 'lat': 35.8617, 'lon': 104.1954, 'name': 'Chine'},
        'china': {'code': 'CN', 'lat': 35.8617, 'lon': 104.1954, 'name': 'Chine'},
        'brésil': {'code': 'BR', 'lat': -14.2350, 'lon': -51.9253, 'name': 'Brésil'},
        'brazil': {'code': 'BR', 'lat': -14.2350, 'lon': -51.9253, 'name': 'Brésil'},
        'inde': {'code': 'IN', 'lat': 20.5937, 'lon': 78.9629, 'name': 'Inde'},
        'india': {'code': 'IN', 'lat': 20.5937, 'lon': 78.9629, 'name': 'Inde'},
        'australie': {'code': 'AU', 'lat': -25.2744, 'lon': 133.7751, 'name': 'Australie'},
        'australia': {'code': 'AU', 'lat': -25.2744, 'lon': 133.7751, 'name': 'Australie'},
        'mexique': {'code': 'MX', 'lat': 23.6345, 'lon': -102.5528, 'name': 'Mexique'},
        'mexico': {'code': 'MX', 'lat': 23.6345, 'lon': -102.5528, 'name': 'Mexique'},
        'suisse': {'code': 'CH', 'lat': 46.8182, 'lon': 8.2275, 'name': 'Suisse'},
        'switzerland': {'code': 'CH', 'lat': 46.8182, 'lon': 8.2275, 'name': 'Suisse'},
        'belgique': {'code': 'BE', 'lat': 50.5039, 'lon': 4.4699, 'name': 'Belgique'},
        'belgium': {'code': 'BE', 'lat': 50.5039, 'lon': 4.4699, 'name': 'Belgique'},
        'pays-bas': {'code': 'NL', 'lat': 52.1326, 'lon': 5.2913, 'name': 'Pays-Bas'},
        'netherlands': {'code': 'NL', 'lat': 52.1326, 'lon': 5.2913, 'name': 'Pays-Bas'},
        'suède': {'code': 'SE', 'lat': 60.1282, 'lon': 18.6435, 'name': 'Suède'},
        'sweden': {'code': 'SE', 'lat': 60.1282, 'lon': 18.6435, 'name': 'Suède'},
        'portugal': {'code': 'PT', 'lat': 39.3999, 'lon': -8.2245, 'name': 'Portugal'},
        'pologne': {'code': 'PL', 'lat': 51.9194, 'lon': 19.1451, 'name': 'Pologne'},
        'poland': {'code': 'PL', 'lat': 51.9194, 'lon': 19.1451, 'name': 'Pologne'},
        'turquie': {'code': 'TR', 'lat': 38.9637, 'lon': 35.2433, 'name': 'Turquie'},
        'turkey': {'code': 'TR', 'lat': 38.9637, 'lon': 35.2433, 'name': 'Turquie'},
        'corée du sud': {'code': 'KR', 'lat': 35.9078, 'lon': 127.7669, 'name': 'Corée du Sud'},
        'south korea': {'code': 'KR', 'lat': 35.9078, 'lon': 127.7669, 'name': 'Corée du Sud'},
        'cameroun': {'code': 'CM', 'lat': 7.3697, 'lon': 12.3547, 'name': 'Cameroun'},
        'cameroon': {'code': 'CM', 'lat': 7.3697, 'lon': 12.3547, 'name': 'Cameroun'},
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_country_from_text(self, text: str) -> Optional[str]:
        """
        Détecter un pays mentionné dans un texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Code pays ISO ou None
        """
        text_lower = text.lower()
        
        # Chercher des mentions de pays
        for country_name, data in self.COUNTRY_DATA.items():
            if country_name in text_lower:
                return data['code']
        
        return None
    
    def get_geographic_distribution(
        self,
        days: int = 30,
        keyword: str = None
    ) -> List[Dict]:
        """
        Obtenir la distribution géographique des mentions
        
        Args:
            days: Période d'analyse en jours
            keyword: Filtrer par mot-clé (optionnel)
            
        Returns:
            Liste des pays avec le nombre de mentions
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer les mentions
        query = self.db.query(Mention).filter(
            Mention.published_at >= since_date
        )
        
        if keyword:
            from app.models import Keyword
            keyword_obj = self.db.query(Keyword).filter(
                Keyword.keyword == keyword
            ).first()
            if keyword_obj:
                query = query.filter(Mention.keyword_id == keyword_obj.id)
        
        mentions = query.all()
        
        # Détecter les pays
        country_counts = Counter()
        country_details = {}
        
        for mention in mentions:
            # Analyser titre et contenu
            text = f"{mention.title} {mention.content}"
            country_code = self.detect_country_from_text(text)
            
            if country_code:
                country_counts[country_code] += 1
                
                # Stocker les détails du pays
                if country_code not in country_details:
                    for country_name, data in self.COUNTRY_DATA.items():
                        if data['code'] == country_code:
                            country_details[country_code] = data
                            break
        
        # Formater les résultats
        results = []
        for country_code, count in country_counts.most_common():
            if country_code in country_details:
                data = country_details[country_code]
                results.append({
                    'country_code': country_code,
                    'country_name': data['name'],
                    'latitude': data['lat'],
                    'longitude': data['lon'],
                    'mention_count': count,
                    'percentage': round((count / len(mentions)) * 100, 2) if mentions else 0
                })
        
        return results
    
    def get_heatmap_data(self, days: int = 30) -> List[Dict]:
        """
        Obtenir les données pour la heatmap
        
        Args:
            days: Période d'analyse en jours
            
        Returns:
            Données formatées pour Leaflet
        """
        distribution = self.get_geographic_distribution(days=days)
        
        # Calculer l'intensité max pour normalisation
        max_count = max([d['mention_count'] for d in distribution]) if distribution else 1
        
        heatmap_data = []
        for item in distribution:
            heatmap_data.append({
                'lat': item['latitude'],
                'lon': item['longitude'],
                'intensity': item['mention_count'] / max_count,
                'count': item['mention_count'],
                'country': item['country_name'],
                'country_code': item['country_code']
            })
        
        return heatmap_data
    
    def get_top_countries(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """
        Obtenir les pays avec le plus de mentions
        
        Args:
            days: Période d'analyse
            limit: Nombre de pays à retourner
            
        Returns:
            Liste des top pays
        """
        distribution = self.get_geographic_distribution(days=days)
        
        # Trier par nombre de mentions
        sorted_countries = sorted(
            distribution,
            key=lambda x: x['mention_count'],
            reverse=True
        )
        
        return sorted_countries[:limit]
    
    def get_country_trends(
        self,
        country_code: str,
        days: int = 30
    ) -> Dict:
        """
        Obtenir les tendances pour un pays spécifique
        
        Args:
            country_code: Code ISO du pays
            days: Période d'analyse
            
        Returns:
            Données de tendance
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Trouver le nom du pays
        country_name = None
        for name, data in self.COUNTRY_DATA.items():
            if data['code'] == country_code:
                country_name = data['name']
                break
        
        if not country_name:
            return {}
        
        # Récupérer les mentions
        mentions = self.db.query(Mention).filter(
            Mention.published_at >= since_date
        ).all()
        
        # Filtrer par pays
        country_mentions = []
        for mention in mentions:
            text = f"{mention.title} {mention.content}"
            detected_code = self.detect_country_from_text(text)
            if detected_code == country_code:
                country_mentions.append(mention)
        
        # Analyser sentiment
        sentiment_dist = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        
        for mention in country_mentions:
            if mention.sentiment:
                sentiment_dist[mention.sentiment] += 1
        
        # Sources
        source_dist = Counter([m.source for m in country_mentions])
        
        return {
            'country_code': country_code,
            'country_name': country_name,
            'total_mentions': len(country_mentions),
            'sentiment_distribution': sentiment_dist,
            'top_sources': dict(source_dist.most_common(5)),
            'avg_engagement': sum(m.engagement_score for m in country_mentions) / len(country_mentions) if country_mentions else 0
        }