"""
Configuration des paramètres d'analyse de risque et de génération de rapports enrichis
Superviseur MINDEF - Version 3.0
"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class RiskAssessmentConfig:
    """Configuration de l'évaluation de risque"""
    
    # Poids des facteurs de risque (total = 100%)
    VOLUME_WEIGHT = 25          # % pour le volume de mentions
    SENTIMENT_WEIGHT = 30       # % pour le sentiment négatif
    ENGAGEMENT_WEIGHT = 20      # % pour l'engagement
    SPIKE_WEIGHT = 15          # % pour les pics d'activité
    DIVERSITY_WEIGHT = 10       # % pour la diversité des sources
    
    # Seuils de normalisation
    MAX_MENTIONS_PER_DAY = 10   # 10 mentions/jour = score volume max (100%)
    MAX_ENGAGEMENT_SCORE = 2000 # Score d'engagement normalisé
    MAX_SPIKE_RATIO = 5.0       # Pic 5x la moyenne = score max
    MAX_SOURCES_COUNT = 5       # 5+ sources différentes = score max
    
    # Seuils de niveau de risque
    HIGH_RISK_THRESHOLD = 70    # >= 70 = ÉLEVÉ
    MEDIUM_RISK_THRESHOLD = 40  # 40-69 = MODÉRÉ
    # < 40 = FAIBLE
    
    # Couleurs associées
    RISK_COLORS = {
        'ÉLEVÉ': '#ef4444',     # Rouge
        'MODÉRÉ': '#f59e0b',    # Orange
        'FAIBLE': '#10b981'     # Vert
    }

@dataclass
class TrendAnalysisConfig:
    """Configuration de l'analyse des tendances"""
    
    # Détection de pics
    PEAK_DETECTION_STDDEV = 2.0     # Nombre d'écarts-types pour détecter un pic
    MIN_PEAK_MENTIONS = 3           # Minimum de mentions pour considérer un pic
    PEAK_FALLBACK_MULTIPLIER = 1.5  # Multiplicateur si pas assez de données pour stddev
    
    # Analyse de tendance
    TREND_INCREASE_THRESHOLD = 1.2  # +20% = tendance croissante
    TREND_DECREASE_THRESHOLD = 0.8  # -20% = tendance décroissante
    
    # Déclencheurs possibles (pour l'analyse manuelle)
    POSSIBLE_TRIGGERS = [
        "Article de presse majeur",
        "Déclaration officielle",
        "Événement médiatique",
        "Publication virale",
        "Réaction en chaîne sur réseaux sociaux",
        "Intervention de personnalité publique",
        "Actualité internationale",
        "Événement politique interne"
    ]

@dataclass
class InfluencerAnalysisConfig:
    """Configuration de l'analyse des influenceurs"""
    
    # Estimation des followers par plateforme (ratio engagement/followers moyen)
    ENGAGEMENT_RATIOS = {
        'youtube': 0.02,    # 2%
        'tiktok': 0.05,     # 5%
        'instagram': 0.03,  # 3%
        'twitter': 0.01,    # 1%
        'reddit': 0.1,      # 10% (upvotes/subscribers)
        'telegram': 0.02,   # 2%
        'facebook': 0.015,  # 1.5%
        'linkedin': 0.02    # 2%
    }
    
    # Seuils de portée
    REACH_THRESHOLDS = {
        'TRÈS ÉLEVÉE': 10000,
        'ÉLEVÉE': 1000,
        'MODÉRÉE': 100,
        'FAIBLE': 0
    }
    
    # Évaluation du risque influenceur
    INFLUENCER_RISK_SENTIMENT_WEIGHT = 0.7  # 70% basé sur sentiment négatif
    INFLUENCER_RISK_ENGAGEMENT_WEIGHT = 0.3 # 30% basé sur niveau d'engagement
    INFLUENCER_HIGH_RISK_THRESHOLD = 0.6    # >= 60% = risque élevé
    INFLUENCER_MEDIUM_RISK_THRESHOLD = 0.3  # 30-60% = risque modéré

@dataclass
class GeographyAnalysisConfig:
    """Configuration de l'analyse géographique"""
    
    # Dictionnaire étendu des pays (peut être enrichi)
    COUNTRY_KEYWORDS = {
        # Europe
        'france': {'code': 'FR', 'lat': 46.2276, 'lon': 2.2137, 'name': 'France'},
        'allemagne': {'code': 'DE', 'lat': 51.1657, 'lon': 10.4515, 'name': 'Allemagne'},
        'espagne': {'code': 'ES', 'lat': 40.4637, 'lon': -3.7492, 'name': 'Espagne'},
        'italie': {'code': 'IT', 'lat': 41.8719, 'lon': 12.5674, 'name': 'Italie'},
        'royaume-uni': {'code': 'GB', 'lat': 55.3781, 'lon': -3.4360, 'name': 'Royaume-Uni'},
        
        # Amérique
        'états-unis': {'code': 'US', 'lat': 37.0902, 'lon': -95.7129, 'name': 'États-Unis'},
        'canada': {'code': 'CA', 'lat': 56.1304, 'lon': -106.3468, 'name': 'Canada'},
        'brésil': {'code': 'BR', 'lat': -14.2350, 'lon': -51.9253, 'name': 'Brésil'},
        'mexique': {'code': 'MX', 'lat': 23.6345, 'lon': -102.5528, 'name': 'Mexique'},
        
        # Asie
        'chine': {'code': 'CN', 'lat': 35.8617, 'lon': 104.1954, 'name': 'Chine'},
        'japon': {'code': 'JP', 'lat': 36.2048, 'lon': 138.2529, 'name': 'Japon'},
        'inde': {'code': 'IN', 'lat': 20.5937, 'lon': 78.9629, 'name': 'Inde'},
        'corée du sud': {'code': 'KR', 'lat': 35.9078, 'lon': 127.7669, 'name': 'Corée du Sud'},
        
        # Afrique
        'cameroun': {'code': 'CM', 'lat': 7.3697, 'lon': 12.3547, 'name': 'Cameroun'},
        'nigeria': {'code': 'NG', 'lat': 9.0820, 'lon': 8.6753, 'name': 'Nigeria'},
        'afrique du sud': {'code': 'ZA', 'lat': -30.5595, 'lon': 22.9375, 'name': 'Afrique du Sud'},
        
        # Autres
        'australie': {'code': 'AU', 'lat': -25.2744, 'lon': 133.7751, 'name': 'Australie'}
    }
    
    # Seuils de risque géographique
    GEO_RISK_NEGATIVE_WEIGHT = 0.6     # 60% basé sur ratio de mentions négatives
    GEO_RISK_DENSITY_WEIGHT = 0.4      # 40% basé sur densité de mentions
    GEO_HIGH_RISK_THRESHOLD = 0.3      # >= 30% = pays à risque

@dataclass
class RecommendationConfig:
    """Configuration des recommandations opérationnelles"""
    
    # Priorités des recommandations
    PRIORITY_LEVELS = {
        1: 'URGENT',      # Action immédiate requise
        2: 'ÉLEVÉE',      # Action dans les 24-48h
        3: 'MOYENNE'      # Action dans la semaine
    }
    
    # Catégories de recommandations
    RECOMMENDATION_CATEGORIES = {
        'URGENT': {
            'icon': '🚨',
            'color': '#ef4444',
            'description': 'Intervention immédiate requise'
        },
        'COMMUNICATION': {
            'icon': '📢', 
            'color': '#3b82f6',
            'description': 'Actions de communication prioritaires'
        },
        'INFLUENCEURS': {
            'icon': '👑',
            'color': '#8b5cf6',
            'description': 'Gestion des comptes influents'
        },
        'GÉOGRAPHIQUE': {
            'icon': '🌍',
            'color': '#10b981',
            'description': 'Actions ciblées par zone'
        },
        'TEMPOREL': {
            'icon': '📊',
            'color': '#f59e0b',
            'description': 'Gestion des pics d\'activité'
        },
        'CONTENU': {
            'icon': '💬',
            'color': '#06b6d4',
            'description': 'Stratégie de contenu'
        },
        'SURVEILLANCE': {
            'icon': '🔍',
            'color': '#6b7280',
            'description': 'Optimisation du monitoring'
        }
    }
    
    # Seuils pour déclencher des recommandations automatiques
    AUTO_RECOMMENDATIONS = {
        'high_risk': {
            'condition': 'risk_level == ÉLEVÉ',
            'categories': ['URGENT', 'COMMUNICATION']
        },
        'negative_influencers': {
            'condition': 'high_risk_influencers > 0',
            'categories': ['INFLUENCEURS']
        },
        'geographic_concentration': {
            'condition': 'risk_countries > 0',
            'categories': ['GÉOGRAPHIQUE']
        },
        'activity_spikes': {
            'condition': 'peaks > 2',
            'categories': ['TEMPOREL']
        },
        'negative_content': {
            'condition': 'negative_content_ratio > 0.3',
            'categories': ['CONTENU']
        }
    }

@dataclass
class ReportGenerationConfig:
    """Configuration générale de génération de rapports"""
    
    # Templates prédéfinis
    REPORT_TEMPLATES = {
        'executive_summary': {
            'name': 'Résumé Exécutif',
            'description': 'Rapport concis pour décideurs (2 pages)',
            'sections': ['analysis', 'risk_assessment', 'recommendations'],
            'default_period': 14,
            'audience': 'Direction générale'
        },
        'crisis_management': {
            'name': 'Gestion de Crise',
            'description': 'Analyse complète pour situation critique',
            'sections': ['risk_assessment', 'trends', 'key_content', 'detailed_influencers', 'recommendations'],
            'default_period': 7,
            'audience': 'Cellule de crise'
        },
        'strategic_analysis': {
            'name': 'Analyse Stratégique',
            'description': 'Rapport complet avec comparaisons (4-5 pages)',
            'sections': ['analysis', 'risk_assessment', 'trends', 'detailed_influencers', 'geography', 'comparison', 'recommendations'],
            'default_period': 30,
            'audience': 'État-major, analystes'
        },
        'influence_mapping': {
            'name': 'Cartographie d\'Influence',
            'description': 'Focus sur les acteurs clés et géographie',
            'sections': ['detailed_influencers', 'geography', 'key_content', 'recommendations'],
            'default_period': 21,
            'audience': 'Service influence'
        }
    }
    
    # Sections disponibles
    AVAILABLE_SECTIONS = {
        'analysis': {
            'name': 'Analyse de Base',
            'description': 'Questions stratégiques et synthèse générale',
            'icon': '📊',
            'required': True
        },
        'risk_assessment': {
            'name': 'Évaluation de Gravité',
            'description': 'Note de risque avec facteurs détaillés',
            'icon': '🚨',
            'required': False
        },
        'trends': {
            'name': 'Analyse des Tendances',
            'description': 'Graphiques temporels et détection de pics',
            'icon': '📈',
            'required': False
        },
        'key_content': {
            'name': 'Contenus Clés',
            'description': 'Publications engageantes et arguments récurrents',
            'icon': '💬',
            'required': False
        },
        'detailed_influencers': {
            'name': 'Profils Détaillés Influenceurs',
            'description': 'Métriques avancées et évolution du ton',
            'icon': '👑',
            'required': False
        },
        'geography': {
            'name': 'Répartition Géographique',
            'description': 'Provenance des mentions par pays/régions',
            'icon': '🌍',
            'required': False
        },
        'comparison': {
            'name': 'Comparaison Temporelle',
            'description': 'Évolution vs période précédente',
            'icon': '📊',
            'required': False
        },
        'recommendations': {
            'name': 'Recommandations Opérationnelles',
            'description': 'Suggestions concrètes d\'actions prioritaires',
            'icon': '🎯',
            'required': False
        }
    }
    
    # Limites et contraintes
    MAX_KEYWORDS_PER_REPORT = 10       # Maximum 10 mots-clés par rapport
    MAX_ANALYSIS_PERIOD_DAYS = 365     # Maximum 1 an d'analyse
    MIN_ANALYSIS_PERIOD_DAYS = 1       # Minimum 1 jour
    
    # Paramètres de style
    REPORT_STYLE = {
        'primary_color': '#667eea',
        'secondary_color': '#764ba2',
        'success_color': '#10b981',
        'warning_color': '#f59e0b',
        'danger_color': '#ef4444',
        'font_family': 'Segoe UI, Arial, sans-serif',
        'font_size_base': '11pt',
        'font_size_title': '20pt',
        'font_size_section': '14pt'
    }

# Instance globale de configuration (peut être modifiée par l'utilisateur)
RISK_CONFIG = RiskAssessmentConfig()
TREND_CONFIG = TrendAnalysisConfig()
INFLUENCER_CONFIG = InfluencerAnalysisConfig()
GEOGRAPHY_CONFIG = GeographyAnalysisConfig()
RECOMMENDATION_CONFIG = RecommendationConfig()
REPORT_CONFIG = ReportGenerationConfig()

def update_risk_thresholds(high: int = 70, medium: int = 40):
    """
    Mettre à jour les seuils de risque
    
    Args:
        high: Seuil pour risque élevé (défaut 70)
        medium: Seuil pour risque modéré (défaut 40)
    """
    global RISK_CONFIG
    RISK_CONFIG.HIGH_RISK_THRESHOLD = high
    RISK_CONFIG.MEDIUM_RISK_THRESHOLD = medium

def update_spike_sensitivity(stddev_multiplier: float = 2.0):
    """
    Mettre à jour la sensibilité de détection des pics
    
    Args:
        stddev_multiplier: Multiplicateur d'écart-type (défaut 2.0)
    """
    global TREND_CONFIG
    TREND_CONFIG.PEAK_DETECTION_STDDEV = stddev_multiplier

def add_country(keyword: str, country_code: str, name: str, lat: float, lon: float):
    """
    Ajouter un nouveau pays à la détection géographique
    
    Args:
        keyword: Mot-clé de détection (ex: 'suisse')
        country_code: Code ISO du pays (ex: 'CH')
        name: Nom affiché (ex: 'Suisse')
        lat: Latitude
        lon: Longitude
    """
    global GEOGRAPHY_CONFIG
    GEOGRAPHY_CONFIG.COUNTRY_KEYWORDS[keyword.lower()] = {
        'code': country_code,
        'lat': lat,
        'lon': lon,
        'name': name
    }

def get_config_summary() -> Dict:
    """
    Obtenir un résumé de la configuration actuelle
    
    Returns:
        Dict avec les paramètres principaux
    """
    return {
        'risk_assessment': {
            'weights': {
                'volume': RISK_CONFIG.VOLUME_WEIGHT,
                'sentiment': RISK_CONFIG.SENTIMENT_WEIGHT,
                'engagement': RISK_CONFIG.ENGAGEMENT_WEIGHT,
                'spike': RISK_CONFIG.SPIKE_WEIGHT,
                'diversity': RISK_CONFIG.DIVERSITY_WEIGHT
            },
            'thresholds': {
                'high': RISK_CONFIG.HIGH_RISK_THRESHOLD,
                'medium': RISK_CONFIG.MEDIUM_RISK_THRESHOLD
            }
        },
        'trend_analysis': {
            'peak_detection_stddev': TREND_CONFIG.PEAK_DETECTION_STDDEV,
            'trend_thresholds': {
                'increase': TREND_CONFIG.TREND_INCREASE_THRESHOLD,
                'decrease': TREND_CONFIG.TREND_DECREASE_THRESHOLD
            }
        },
        'geography': {
            'countries_count': len(GEOGRAPHY_CONFIG.COUNTRY_KEYWORDS),
            'risk_weights': {
                'negative_ratio': GEOGRAPHY_CONFIG.GEO_RISK_NEGATIVE_WEIGHT,
                'density': GEOGRAPHY_CONFIG.GEO_RISK_DENSITY_WEIGHT
            }
        },
        'report_generation': {
            'templates_count': len(REPORT_CONFIG.REPORT_TEMPLATES),
            'sections_count': len(REPORT_CONFIG.AVAILABLE_SECTIONS),
            'max_keywords': REPORT_CONFIG.MAX_KEYWORDS_PER_REPORT
        }
    }

# Exemple d'utilisation personnalisée
if __name__ == "__main__":
    # Exemple de personnalisation des seuils
    print("Configuration par défaut:")
    print(get_config_summary())
    
    # Modifier les seuils de risque pour être plus sensible
    update_risk_thresholds(high=60, medium=30)
    
    # Réduire la sensibilité des pics
    update_spike_sensitivity(2.5)
    
    # Ajouter un nouveau pays
    add_country('suisse', 'CH', 'Suisse', 46.8182, 8.2275)
    
    print("\nConfiguration personnalisée:")
    print(get_config_summary())