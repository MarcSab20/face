"""
Service de génération de rapports PDF professionnels - Version 3
Avec analyse détaillée, évaluation de risque et recommandations opérationnelles
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from collections import Counter
import statistics

logger = logging.getLogger(__name__)


class ReportGeneratorEnhanced:
    """Générateur de rapports PDF avec analyse intelligente et évaluation de risque"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_enhanced_report(
        self,
        keyword_ids: List[int],
        days: int = 30,
        report_object: str = "",
        include_sections: List[str] = None
    ) -> Dict:
        """
        Générer un rapport complet avec analyse de risque et recommandations
        
        Args:
            keyword_ids: Liste des IDs de mots-clés
            days: Période d'analyse en jours
            report_object: Objet/sujet du rapport
            include_sections: Sections à inclure
            
        Returns:
            Dict avec les données du rapport enrichi
        """
        from app.models import Keyword, Mention
        from app.influencer_analyzer import InfluencerAnalyzer
        from app.geo_analyzer import GeoAnalyzer
        
        # Sections par défaut étendues
        if include_sections is None:
            include_sections = ['analysis', 'risk_assessment', 'trends', 'key_content', 
                              'detailed_influencers', 'geography', 'comparison', 'recommendations']
        
        # Récupérer les mots-clés
        keywords = self.db.query(Keyword).filter(
            Keyword.id.in_(keyword_ids)
        ).all()
        
        if not keywords:
            raise ValueError(f"Aucun mot-clé trouvé")
        
        keywords_names = [kw.keyword for kw in keywords]
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer toutes les mentions pour ces mots-clés
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).order_by(desc(Mention.published_at)).all()
        
        report_data = {
            'keywords': keywords_names,
            'keyword_ids': keyword_ids,
            'period_days': days,
            'report_object': report_object or ', '.join(keywords_names),
            'generated_at': datetime.utcnow(),
            'total_mentions': len(mentions),
        }
        
        # 1. Analyse de base
        if 'analysis' in include_sections:
            report_data['analysis'] = self._generate_detailed_analysis(
                mentions, keywords_names, days
            )
        
        # 2. Évaluation de la gravité/risque
        if 'risk_assessment' in include_sections:
            report_data['risk_assessment'] = self._generate_risk_assessment(
                mentions, days
            )
        
        # 3. Analyse des tendances avec graphique de pic
        if 'trends' in include_sections:
            report_data['trends'] = self._generate_trends_analysis(
                mentions, days
            )
        
        # 4. Commentaires/publications clés
        if 'key_content' in include_sections:
            report_data['key_content'] = self._extract_key_content(mentions)
        
        # 5. Profil détaillé des influenceurs
        if 'detailed_influencers' in include_sections:
            analyzer = InfluencerAnalyzer(self.db)
            report_data['detailed_influencers'] = self._generate_detailed_influencers(
                analyzer, keyword_ids, days
            )
        
        # 6. Répartition géographique
        if 'geography' in include_sections:
            geo_analyzer = GeoAnalyzer(self.db)
            report_data['geography'] = self._generate_geography_analysis(
                geo_analyzer, days, keywords_names
            )
        
        # 7. Comparaison avec période de référence
        if 'comparison' in include_sections:
            report_data['comparison'] = self._generate_comparison_analysis(
                keyword_ids, days
            )
        
        # 8. Recommandations opérationnelles
        if 'recommendations' in include_sections:
            report_data['recommendations'] = self._generate_operational_recommendations(
                mentions, report_data
            )
        
        return report_data
    
    def _generate_risk_assessment(self, mentions: List, days: int) -> Dict:
        """
        Évaluation de la gravité avec note de risque
        """
        if not mentions:
            return {
                'risk_level': 'FAIBLE',
                'risk_score': 0,
                'explanation': 'Aucune mention détectée sur la période.',
                'factors': {}
            }
        
        # Facteurs de risque
        total_mentions = len(mentions)
        
        # 1. Volume de mentions
        volume_score = min(total_mentions / (days * 10), 1.0)  # 10 mentions/jour = score max
        
        # 2. Sentiment négatif
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        negative_ratio = len(negative_mentions) / total_mentions if total_mentions > 0 else 0
        sentiment_score = negative_ratio
        
        # 3. Engagement élevé
        if mentions:
            avg_engagement = sum(m.engagement_score for m in mentions) / len(mentions)
            max_engagement = max(m.engagement_score for m in mentions)
            engagement_score = min((avg_engagement + max_engagement) / 2000, 1.0)  # Normalisation
        else:
            engagement_score = 0
        
        # 4. Concentration temporelle (pics)
        timeline = {}
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date()
                timeline[date_key] = timeline.get(date_key, 0) + 1
        
        if timeline:
            daily_counts = list(timeline.values())
            avg_daily = statistics.mean(daily_counts)
            max_daily = max(daily_counts)
            spike_score = min((max_daily / (avg_daily + 1)) / 5, 1.0)  # Pic 5x la moyenne = score max
        else:
            spike_score = 0
        
        # 5. Diversité des sources
        sources = set(m.source for m in mentions)
        source_diversity_score = min(len(sources) / 5, 1.0)  # 5+ sources = score max
        
        # Score global de risque (0-100)
        risk_score = (
            volume_score * 25 +           # 25% pour le volume
            sentiment_score * 30 +        # 30% pour le sentiment
            engagement_score * 20 +       # 20% pour l'engagement
            spike_score * 15 +           # 15% pour les pics
            source_diversity_score * 10   # 10% pour la diversité
        )
        
        # Déterminer le niveau de risque
        if risk_score >= 70:
            risk_level = 'ÉLEVÉ'
            color = '#ef4444'
        elif risk_score >= 40:
            risk_level = 'MODÉRÉ'
            color = '#f59e0b'
        else:
            risk_level = 'FAIBLE'
            color = '#10b981'
        
        # Explication détaillée
        explanation = self._generate_risk_explanation(
            risk_level, volume_score, sentiment_score, engagement_score, 
            spike_score, source_diversity_score, total_mentions, negative_ratio
        )
        
        return {
            'risk_level': risk_level,
            'risk_score': round(risk_score, 1),
            'color': color,
            'explanation': explanation,
            'factors': {
                'volume': {'score': round(volume_score * 100, 1), 'weight': '25%'},
                'sentiment': {'score': round(sentiment_score * 100, 1), 'weight': '30%'},
                'engagement': {'score': round(engagement_score * 100, 1), 'weight': '20%'},
                'spike': {'score': round(spike_score * 100, 1), 'weight': '15%'},
                'diversity': {'score': round(source_diversity_score * 100, 1), 'weight': '10%'}
            },
            'metrics': {
                'total_mentions': total_mentions,
                'negative_ratio': round(negative_ratio * 100, 1),
                'sources_count': len(sources),
                'max_daily_mentions': max(timeline.values()) if timeline else 0
            }
        }
    
    def _generate_trends_analysis(self, mentions: List, days: int) -> Dict:
        """
        Analyse des tendances avec détection de pics
        """
        # Timeline jour par jour
        timeline = {}
        sentiment_timeline = {}
        
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date()
                timeline[date_key] = timeline.get(date_key, 0) + 1
                
                if date_key not in sentiment_timeline:
                    sentiment_timeline[date_key] = {'positive': 0, 'neutral': 0, 'negative': 0}
                
                if mention.sentiment:
                    sentiment_timeline[date_key][mention.sentiment] += 1
        
        # Compléter les jours manquants
        start_date = datetime.utcnow().date() - timedelta(days=days)
        daily_data = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            mentions_count = timeline.get(current_date, 0)
            sentiment_data = sentiment_timeline.get(current_date, {'positive': 0, 'neutral': 0, 'negative': 0})
            
            daily_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'date_display': current_date.strftime('%d/%m'),
                'mentions': mentions_count,
                'positive': sentiment_data['positive'],
                'neutral': sentiment_data['neutral'],
                'negative': sentiment_data['negative']
            })
        
        # Détection des pics
        mentions_counts = [d['mentions'] for d in daily_data]
        avg_mentions = statistics.mean(mentions_counts) if mentions_counts else 0
        std_dev = statistics.stdev(mentions_counts) if len(mentions_counts) > 1 else 0
        
        # Un pic = 2 écarts-types au-dessus de la moyenne
        peak_threshold = avg_mentions + (2 * std_dev) if std_dev > 0 else avg_mentions * 1.5
        
        peaks = []
        for data in daily_data:
            if data['mentions'] > peak_threshold and data['mentions'] > 0:
                peaks.append({
                    'date': data['date'],
                    'date_display': data['date_display'],
                    'mentions': data['mentions'],
                    'intensity': round((data['mentions'] / peak_threshold), 2) if peak_threshold > 0 else 1
                })
        
        # Analyse des pics
        peak_analysis = self._analyze_peaks(peaks, daily_data, mentions)
        
        # Tendance générale
        if len(mentions_counts) >= 2:
            first_half = mentions_counts[:len(mentions_counts)//2]
            second_half = mentions_counts[len(mentions_counts)//2:]
            
            first_avg = statistics.mean(first_half) if first_half else 0
            second_avg = statistics.mean(second_half) if second_half else 0
            
            if second_avg > first_avg * 1.2:
                trend = 'CROISSANTE'
                trend_icon = '📈'
            elif second_avg < first_avg * 0.8:
                trend = 'DÉCROISSANTE'
                trend_icon = '📉'
            else:
                trend = 'STABLE'
                trend_icon = '➡️'
        else:
            trend = 'INSUFFISANT'
            trend_icon = '❓'
        
        return {
            'daily_data': daily_data,
            'peaks': peaks,
            'peak_analysis': peak_analysis,
            'trend': trend,
            'trend_icon': trend_icon,
            'statistics': {
                'avg_daily_mentions': round(avg_mentions, 1),
                'max_daily_mentions': max(mentions_counts) if mentions_counts else 0,
                'peak_threshold': round(peak_threshold, 1),
                'total_peaks': len(peaks)
            }
        }
    
    def _extract_key_content(self, mentions: List) -> Dict:
        """
        Extraire les commentaires et publications clés
        """
        # Trier par engagement décroissant
        top_engaged = sorted(mentions, key=lambda m: m.engagement_score, reverse=True)[:10]
        
        # Analyser les contenus par sentiment
        content_by_sentiment = {
            'positive': [],
            'negative': [],
            'neutral': []
        }
        
        for mention in top_engaged:
            if mention.sentiment and mention.sentiment in content_by_sentiment:
                content_by_sentiment[mention.sentiment].append({
                    'title': mention.title,
                    'content': mention.content[:300] + '...' if len(mention.content) > 300 else mention.content,
                    'author': mention.author,
                    'source': mention.source,
                    'engagement': mention.engagement_score,
                    'url': mention.source_url,
                    'published_at': mention.published_at.strftime('%d/%m/%Y') if mention.published_at else 'Date inconnue'
                })
        
        # Arguments récurrents
        all_content = ' '.join([m.title + ' ' + m.content for m in mentions])
        words = all_content.lower().split()
        word_freq = Counter(word for word in words if len(word) > 4)  # Mots de plus de 4 lettres
        common_themes = word_freq.most_common(10)
        
        return {
            'top_engaged': top_engaged[:5],
            'content_by_sentiment': content_by_sentiment,
            'common_themes': common_themes,
            'total_analyzed': len(top_engaged)
        }
    
    def _generate_detailed_influencers(self, analyzer, keyword_ids: List[int], days: int) -> Dict:
        """
        Profil détaillé des influenceurs avec métriques avancées
        """
        # Récupérer tous les influenceurs
        all_influencers = analyzer.get_top_influencers(days=days, limit=50)
        
        # Filtrer pour ces mots-clés (simulation)
        from app.models import Mention
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= datetime.utcnow() - timedelta(days=days)
        ).all()
        
        relevant_influencers = []
        for influencer in all_influencers:
            # Calculer des métriques supplémentaires
            author_mentions = [m for m in mentions if m.author == influencer['author'] and m.source == influencer['source']]
            
            if author_mentions:
                # Analyse temporelle
                dates = [m.published_at for m in author_mentions if m.published_at]
                if len(dates) >= 2:
                    dates.sort()
                    posting_frequency = len(dates) / ((dates[-1] - dates[0]).days + 1)
                else:
                    posting_frequency = len(dates) / days
                
                # Évolution du ton
                recent_sentiment = []
                older_sentiment = []
                mid_date = datetime.utcnow() - timedelta(days=days//2)
                
                for mention in author_mentions:
                    if mention.sentiment and mention.published_at:
                        if mention.published_at >= mid_date:
                            recent_sentiment.append(mention.sentiment)
                        else:
                            older_sentiment.append(mention.sentiment)
                
                # Calculer l'évolution
                if recent_sentiment and older_sentiment:
                    recent_positive = recent_sentiment.count('positive') / len(recent_sentiment)
                    older_positive = older_sentiment.count('positive') / len(older_sentiment)
                    tone_evolution = recent_positive - older_positive
                else:
                    tone_evolution = 0
                
                # Enrichir les données influenceur
                enhanced_influencer = {
                    **influencer,
                    'posting_frequency': round(posting_frequency, 2),
                    'tone_evolution': round(tone_evolution, 2),
                    'tone_trend': 'Amélioration' if tone_evolution > 0.1 else 'Dégradation' if tone_evolution < -0.1 else 'Stable',
                    'estimated_followers': self._estimate_followers(influencer['source'], influencer['avg_engagement']),
                    'audience_reach': self._calculate_reach_score(influencer['total_engagement'], len(author_mentions)),
                    'risk_level': self._assess_influencer_risk(influencer, author_mentions)
                }
                
                relevant_influencers.append(enhanced_influencer)
        
        return {
            'influencers': relevant_influencers[:15],
            'summary': {
                'total_active': len(relevant_influencers),
                'high_risk': len([i for i in relevant_influencers if i['risk_level'] == 'ÉLEVÉ']),
                'improving_tone': len([i for i in relevant_influencers if i['tone_evolution'] > 0.1]),
                'declining_tone': len([i for i in relevant_influencers if i['tone_evolution'] < -0.1])
            }
        }
    
    def _generate_geography_analysis(self, geo_analyzer, days: int, keywords: List[str]) -> Dict:
        """
        Analyse géographique détaillée
        """
        distribution = geo_analyzer.get_geographic_distribution(days=days)
        top_countries = geo_analyzer.get_top_countries(days=days, limit=10)
        
        # Analyse des risques géographiques
        risk_countries = []
        for country in top_countries:
            trends = geo_analyzer.get_country_trends(country['country_code'], days=days)
            
            # Calculer le score de risque géographique
            negative_ratio = trends.get('sentiment_distribution', {}).get('negative', 0) / max(trends.get('total_mentions', 1), 1)
            mention_density = country['mention_count'] / max(sum(c['mention_count'] for c in distribution), 1)
            
            risk_score = (negative_ratio * 0.6) + (mention_density * 0.4)
            
            if risk_score > 0.3:
                risk_countries.append({
                    'country': country['country_name'],
                    'risk_score': round(risk_score, 2),
                    'mentions': country['mention_count'],
                    'negative_ratio': round(negative_ratio * 100, 1)
                })
        
        return {
            'distribution': distribution,
            'top_countries': top_countries,
            'risk_countries': risk_countries,
            'total_countries': len(distribution),
            'concentration_ratio': round(sum(c['mention_count'] for c in top_countries[:3]) / max(sum(c['mention_count'] for c in distribution), 1) * 100, 1)
        }
    
    def _generate_comparison_analysis(self, keyword_ids: List[int], days: int) -> Dict:
        """
        Comparaison avec période de référence
        """
        from app.models import Mention
        
        # Période actuelle
        current_end = datetime.utcnow()
        current_start = current_end - timedelta(days=days)
        
        # Période de référence (période précédente de même durée)
        reference_end = current_start
        reference_start = reference_end - timedelta(days=days)
        
        # Mentions période actuelle
        current_mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= current_start,
            Mention.published_at < current_end
        ).all()
        
        # Mentions période de référence
        reference_mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= reference_start,
            Mention.published_at < reference_end
        ).all()
        
        # Calculer les métriques comparatives
        current_count = len(current_mentions)
        reference_count = len(reference_mentions)
        
        # Volume
        volume_change = ((current_count - reference_count) / max(reference_count, 1)) * 100
        
        # Sentiment
        current_negative = len([m for m in current_mentions if m.sentiment == 'negative'])
        reference_negative = len([m for m in reference_mentions if m.sentiment == 'negative'])
        
        current_negative_ratio = current_negative / max(current_count, 1)
        reference_negative_ratio = reference_negative / max(reference_count, 1)
        sentiment_change = current_negative_ratio - reference_negative_ratio
        
        # Engagement
        current_avg_engagement = sum(m.engagement_score for m in current_mentions) / max(current_count, 1)
        reference_avg_engagement = sum(m.engagement_score for m in reference_mentions) / max(reference_count, 1)
        engagement_change = ((current_avg_engagement - reference_avg_engagement) / max(reference_avg_engagement, 1)) * 100
        
        # Sources
        current_sources = set(m.source for m in current_mentions)
        reference_sources = set(m.source for m in reference_mentions)
        new_sources = current_sources - reference_sources
        lost_sources = reference_sources - current_sources
        
        return {
            'current_period': {
                'start': current_start.strftime('%d/%m/%Y'),
                'end': current_end.strftime('%d/%m/%Y'),
                'mentions': current_count,
                'avg_engagement': round(current_avg_engagement, 1),
                'negative_ratio': round(current_negative_ratio * 100, 1)
            },
            'reference_period': {
                'start': reference_start.strftime('%d/%m/%Y'),
                'end': reference_end.strftime('%d/%m/%Y'),
                'mentions': reference_count,
                'avg_engagement': round(reference_avg_engagement, 1),
                'negative_ratio': round(reference_negative_ratio * 100, 1)
            },
            'changes': {
                'volume': round(volume_change, 1),
                'sentiment': round(sentiment_change * 100, 1),
                'engagement': round(engagement_change, 1)
            },
            'sources_evolution': {
                'new_sources': list(new_sources),
                'lost_sources': list(lost_sources),
                'stable_sources': list(current_sources & reference_sources)
            },
            'interpretation': self._interpret_changes(volume_change, sentiment_change, engagement_change)
        }
    
    def _generate_operational_recommendations(self, mentions: List, report_data: Dict) -> Dict:
        """
        Générer des recommandations opérationnelles concrètes
        """
        recommendations = []
        
        # 1. Recommandations basées sur le niveau de risque
        risk_level = report_data.get('risk_assessment', {}).get('risk_level', 'FAIBLE')
        
        if risk_level == 'ÉLEVÉ':
            recommendations.extend([
                {
                    'category': 'URGENT',
                    'icon': '🚨',
                    'title': 'Surveillance renforcée',
                    'description': 'Mettre en place une surveillance 24h/24 des mentions négatives',
                    'actions': [
                        'Configurer des alertes temps réel',
                        'Désigner une équipe de veille dédiée',
                        'Préparer des réponses pré-approuvées'
                    ]
                },
                {
                    'category': 'COMMUNICATION',
                    'icon': '📢',
                    'title': 'Réponse proactive',
                    'description': 'Engager rapidement avec les influenceurs négatifs',
                    'actions': [
                        'Contacter directement les influenceurs à fort impact',
                        'Publier des clarifications factuelles',
                        'Mobiliser les supporters existants'
                    ]
                }
            ])
        
        # 2. Recommandations basées sur les influenceurs
        if 'detailed_influencers' in report_data:
            high_risk_influencers = [i for i in report_data['detailed_influencers']['influencers'] 
                                   if i.get('risk_level') == 'ÉLEVÉ']
            
            if high_risk_influencers:
                recommendations.append({
                    'category': 'INFLUENCEURS',
                    'icon': '👑',
                    'title': f'Gestion des influenceurs à risque ({len(high_risk_influencers)})',
                    'description': 'Stratégie ciblée pour les comptes à fort impact négatif',
                    'actions': [
                        f'Surveiller spécifiquement: {", ".join([i["author"] for i in high_risk_influencers[:3]])}',
                        'Préparer des contre-arguments documentés',
                        'Identifier des influenceurs neutres à mobiliser'
                    ]
                })
        
        # 3. Recommandations géographiques
        if 'geography' in report_data:
            risk_countries = report_data['geography'].get('risk_countries', [])
            if risk_countries:
                top_risk = risk_countries[0]
                recommendations.append({
                    'category': 'GÉOGRAPHIQUE',
                    'icon': '🌍',
                    'title': f'Focus sur {top_risk["country"]}',
                    'description': f'Concentration de mentions négatives ({top_risk["negative_ratio"]}%)',
                    'actions': [
                        f'Analyser les médias locaux de {top_risk["country"]}',
                        'Adapter la communication au contexte culturel',
                        'Identifier des relais d\'opinion locaux'
                    ]
                })
        
        # 4. Recommandations temporelles
        if 'trends' in report_data:
            peaks = report_data['trends'].get('peaks', [])
            if peaks:
                recommendations.append({
                    'category': 'TEMPOREL',
                    'icon': '📊',
                    'title': 'Gestion des pics d\'activité',
                    'description': f'{len(peaks)} pic(s) détecté(s) nécessitant une attention',
                    'actions': [
                        'Identifier les déclencheurs de chaque pic',
                        'Préparer des réponses rapides pour les futures occurrences',
                        'Planifier la communication lors des événements similaires'
                    ]
                })
        
        # 5. Recommandations de contenu
        if 'key_content' in report_data:
            negative_content = report_data['key_content']['content_by_sentiment'].get('negative', [])
            if negative_content:
                main_themes = [theme[0] for theme in report_data['key_content']['common_themes'][:3]]
                recommendations.append({
                    'category': 'CONTENU',
                    'icon': '💬',
                    'title': 'Contre-narratifs ciblés',
                    'description': 'Créer du contenu répondant aux arguments négatifs',
                    'actions': [
                        f'Développer des FAQ sur: {", ".join(main_themes)}',
                        'Produire du contenu factuel et accessible',
                        'Utiliser les témoignages positifs existants'
                    ]
                })
        
        # 6. Recommandations de monitoring
        recommendations.append({
            'category': 'SURVEILLANCE',
            'icon': '🔍',
            'title': 'Optimisation du monitoring',
            'description': 'Améliorer la collecte et l\'analyse des données',
            'actions': [
                'Étendre la surveillance aux sources émergentes',
                'Affiner les mots-clés de surveillance',
                'Automatiser les alertes selon les seuils de risque'
            ]
        })
        
        # Score de priorité pour chaque recommandation
        for i, rec in enumerate(recommendations):
            if rec['category'] == 'URGENT':
                rec['priority'] = 1
            elif rec['category'] in ['COMMUNICATION', 'INFLUENCEURS']:
                rec['priority'] = 2
            else:
                rec['priority'] = 3
        
        # Trier par priorité
        recommendations.sort(key=lambda x: x['priority'])
        
        return {
            'recommendations': recommendations,
            'summary': {
                'total': len(recommendations),
                'urgent': len([r for r in recommendations if r['priority'] == 1]),
                'high': len([r for r in recommendations if r['priority'] == 2]),
                'medium': len([r for r in recommendations if r['priority'] == 3])
            }
        }
    
    # Méthodes utilitaires
    def _generate_risk_explanation(self, risk_level, volume_score, sentiment_score, 
                                 engagement_score, spike_score, source_diversity_score, 
                                 total_mentions, negative_ratio):
        """Générer l'explication du niveau de risque"""
        
        explanations = []
        
        if volume_score > 0.7:
            explanations.append(f"Volume élevé ({total_mentions} mentions)")
        elif volume_score < 0.3:
            explanations.append("Volume faible de mentions")
        
        if sentiment_score > 0.5:
            explanations.append(f"Sentiment largement négatif ({negative_ratio*100:.0f}%)")
        elif sentiment_score < 0.2:
            explanations.append("Sentiment majoritairement positif")
        
        if engagement_score > 0.6:
            explanations.append("Engagement très élevé")
        
        if spike_score > 0.5:
            explanations.append("Pics d'activité détectés")
        
        if source_diversity_score > 0.8:
            explanations.append("Propagation sur de nombreuses sources")
        
        base_text = f"Niveau de risque {risk_level} déterminé par: "
        return base_text + ", ".join(explanations) + "."
    
    def _analyze_peaks(self, peaks, daily_data, mentions):
        """Analyser les pics d'activité"""
        if not peaks:
            return {
                'summary': 'Aucun pic significatif détecté.',
                'details': [],
                'possible_triggers': []
            }
        
        # Analyser chaque pic
        peak_details = []
        for peak in peaks:
            peak_date = datetime.strptime(peak['date'], '%Y-%m-%d').date()
            
            # Mentions du jour du pic
            peak_mentions = [m for m in mentions 
                           if m.published_at and m.published_at.date() == peak_date]
            
            # Analyse du sentiment du pic
            peak_sentiment = Counter([m.sentiment for m in peak_mentions if m.sentiment])
            dominant_sentiment = peak_sentiment.most_common(1)[0][0] if peak_sentiment else 'unknown'
            
            # Sources principales
            peak_sources = Counter([m.source for m in peak_mentions])
            main_source = peak_sources.most_common(1)[0][0] if peak_sources else 'unknown'
            
            peak_details.append({
                'date': peak['date_display'],
                'mentions': peak['mentions'],
                'intensity': peak['intensity'],
                'dominant_sentiment': dominant_sentiment,
                'main_source': main_source,
                'description': f"Pic de {peak['mentions']} mentions (x{peak['intensity']}) principalement {dominant_sentiment} sur {main_source}"
            })
        
        # Détecter les déclencheurs possibles
        possible_triggers = [
            "Article de presse majeur",
            "Déclaration officielle",
            "Événement médiatique",
            "Publication virale",
            "Réaction en chaîne sur réseaux sociaux"
        ]
        
        summary = f"{len(peaks)} pic(s) détecté(s). " + \
                 f"Le plus important le {peaks[0]['date_display'] if peaks else 'N/A'} " + \
                 f"avec {peaks[0]['mentions'] if peaks else 0} mentions."
        
        return {
            'summary': summary,
            'details': peak_details,
            'possible_triggers': possible_triggers
        }
    
    def _estimate_followers(self, source, avg_engagement):
        """Estimer le nombre d'abonnés basé sur l'engagement"""
        # Ratios moyens engagement/followers par plateforme
        ratios = {
            'youtube': 0.02,    # 2%
            'tiktok': 0.05,     # 5%
            'instagram': 0.03,  # 3%
            'twitter': 0.01,    # 1%
            'reddit': 0.1,      # 10% (upvotes/subscribers)
        }
        
        ratio = ratios.get(source, 0.02)
        estimated = avg_engagement / ratio if ratio > 0 else 0
        
        # Formater le résultat
        if estimated > 1000000:
            return f"{estimated/1000000:.1f}M"
        elif estimated > 1000:
            return f"{estimated/1000:.0f}K"
        else:
            return f"{estimated:.0f}"
    
    def _calculate_reach_score(self, total_engagement, mention_count):
        """Calculer un score de portée"""
        if mention_count == 0:
            return 0
        
        avg_engagement = total_engagement / mention_count
        
        if avg_engagement > 10000:
            return "TRÈS ÉLEVÉE"
        elif avg_engagement > 1000:
            return "ÉLEVÉE"
        elif avg_engagement > 100:
            return "MODÉRÉE"
        else:
            return "FAIBLE"
    
    def _assess_influencer_risk(self, influencer, mentions):
        """Évaluer le niveau de risque d'un influenceur"""
        negative_ratio = influencer['negative_mentions'] / max(influencer['mention_count'], 1)
        engagement_level = influencer['total_engagement']
        
        risk_score = (negative_ratio * 0.7) + (min(engagement_level / 10000, 1) * 0.3)
        
        if risk_score > 0.6:
            return "ÉLEVÉ"
        elif risk_score > 0.3:
            return "MODÉRÉ"
        else:
            return "FAIBLE"
    
    def _interpret_changes(self, volume_change, sentiment_change, engagement_change):
        """Interpréter les changements par rapport à la période de référence"""
        interpretations = []
        
        if abs(volume_change) > 20:
            direction = "augmentation" if volume_change > 0 else "diminution"
            interpretations.append(f"{direction} significative du volume ({volume_change:+.1f}%)")
        
        if abs(sentiment_change) > 0.1:
            direction = "dégradation" if sentiment_change > 0 else "amélioration"
            interpretations.append(f"{direction} du sentiment ({sentiment_change:+.1f} points)")
        
        if abs(engagement_change) > 20:
            direction = "hausse" if engagement_change > 0 else "baisse"
            interpretations.append(f"{direction} de l'engagement ({engagement_change:+.1f}%)")
        
        if not interpretations:
            return "Évolution stable par rapport à la période de référence."
        
        return "Changements notables: " + ", ".join(interpretations) + "."
    
    def _generate_detailed_analysis(self, mentions, keywords, days):
        """Méthode existante adaptée"""
        # Cette méthode reprend la logique existante du rapport de base
        # mais peut être enrichie avec les nouvelles métriques
        
        total = len(mentions)
        
        if total == 0:
            return {
                'is_followed': {
                    'answer': "Aucune mention trouvée",
                    'details': "Il n'y a pas de données sur cette période.",
                    'metrics': {}
                },
                'synthesis': "Aucune activité détectée sur la période analysée."
            }
        
        # Reprise de la logique existante d'analyse...
        # (code existant de _generate_detailed_analysis)
        
        # Analyse du sentiment
        sentiment_dist = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        for mention in mentions:
            if mention.sentiment:
                sentiment_dist[mention.sentiment] = sentiment_dist.get(mention.sentiment, 0) + 1
        
        total_with_sentiment = sum(sentiment_dist.values())
        
        # Calcul des pourcentages
        sentiment_pct = {}
        if total_with_sentiment > 0:
            for key, val in sentiment_dist.items():
                sentiment_pct[key] = (val / total_with_sentiment) * 100
        else:
            sentiment_pct = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        # Calcul de l'engagement
        total_engagement = sum(m.engagement_score for m in mentions)
        avg_engagement = total_engagement / total if total > 0 else 0
        
        # Mentions par jour
        mentions_per_day = total / days
        
        # Distribution temporelle
        timeline = {}
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date()
                timeline[date_key] = timeline.get(date_key, 0) + 1
        
        # Déterminer si c'est suivi (régularité)
        days_with_mentions = len(timeline)
        coverage_pct = (days_with_mentions / days) * 100
        
        # Synthèse simple pour l'instant
        synthesis = f"Sur {days} jours, {total} mentions analysées avec {sentiment_pct.get('positive', 0):.0f}% de sentiment positif."
        
        return {
            'synthesis': synthesis,
            'metrics': {
                'total_mentions': total,
                'mentions_per_day': round(mentions_per_day, 1),
                'coverage_percentage': round(coverage_pct, 1),
                'total_engagement': total_engagement,
                'avg_engagement': round(avg_engagement, 1),
                'sentiment_distribution': sentiment_dist,
                'sentiment_percentages': sentiment_pct
            }
        }

    def generate_enhanced_html_report(self, report_data: Dict) -> str:
        """
        Générer le HTML du rapport enrichi (format 4-5 pages)
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4; margin: 1.5cm; }}
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.4; font-size: 11pt; }}
                .header {{ text-align: center; padding: 15px 0; border-bottom: 3px solid #667eea; margin-bottom: 20px; }}
                .header h1 {{ color: #667eea; font-size: 20pt; margin: 0 0 5px 0; }}
                .header .subtitle {{ color: #666; font-size: 10pt; }}
                .page-break {{ page-break-after: always; }}
                .section-title {{ color: #667eea; font-size: 14pt; font-weight: bold; margin: 20px 0 10px 0; padding-bottom: 5px; border-bottom: 2px solid #e5e7eb; }}
                .risk-box {{ padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 5px solid; }}
                .risk-high {{ background: #fef2f2; border-color: #ef4444; }}
                .risk-medium {{ background: #fffbeb; border-color: #f59e0b; }}
                .risk-low {{ background: #f0fdf4; border-color: #10b981; }}
                .chart-container {{ margin: 20px 0; }}
                .metrics-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0; }}
                .metric-card {{ background: #f9fafb; padding: 15px; border-radius: 8px; text-align: center; }}
                .metric-value {{ font-size: 24pt; font-weight: bold; color: #667eea; }}
                .metric-label {{ font-size: 10pt; color: #6b7280; margin-top: 5px; }}
                .recommendation {{ background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 12px; margin: 10px 0; }}
                .recommendation-title {{ font-weight: bold; color: #1e40af; }}
                .peak-indicator {{ background: #fecaca; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-size: 9pt; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 9pt; }}
                th {{ background: #667eea; color: white; padding: 8px; text-align: left; font-weight: bold; }}
                td {{ padding: 6px 8px; border-bottom: 1px solid #e5e7eb; }}
                tr:nth-child(even) {{ background: #f9fafb; }}
                .footer {{ position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8pt; color: #9ca3af; padding: 10px; border-top: 1px solid #e5e7eb; }}
            </style>
        </head>
        <body>
        """
        
        # Page 1: Vue d'ensemble et évaluation de risque
        html += f"""
            <div class="header">
                <h1>📊 RAPPORT D'ANALYSE AVANCÉ</h1>
                <div class="subtitle">
                    <strong>{report_data['report_object']}</strong><br>
                    Période: {report_data['period_days']} jours | 
                    Généré le: {report_data['generated_at'].strftime('%d/%m/%Y à %H:%M')}
                </div>
            </div>
        """
        
        # Évaluation de risque
        if 'risk_assessment' in report_data:
            risk = report_data['risk_assessment']
            risk_class = f"risk-{risk['risk_level'].lower()}"
            if risk['risk_level'] == 'ÉLEVÉ':
                risk_class = 'risk-high'
            elif risk['risk_level'] == 'MODÉRÉ':
                risk_class = 'risk-medium'
            else:
                risk_class = 'risk-low'
                
            html += f"""
            <div class="section-title">🚨 ÉVALUATION DE LA GRAVITÉ</div>
            <div class="risk-box {risk_class}">
                <h3 style="margin: 0 0 10px 0;">NIVEAU DE RISQUE: {risk['risk_level']} ({risk['risk_score']}/100)</h3>
                <p>{risk['explanation']}</p>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{risk['factors']['volume']['score']}%</div>
                        <div class="metric-label">Volume ({risk['factors']['volume']['weight']})</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{risk['factors']['sentiment']['score']}%</div>
                        <div class="metric-label">Sentiment ({risk['factors']['sentiment']['weight']})</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{risk['factors']['engagement']['score']}%</div>
                        <div class="metric-label">Engagement ({risk['factors']['engagement']['weight']})</div>
                    </div>
                </div>
            </div>
            """
        
        # Analyse des tendances et pics
        if 'trends' in report_data:
            trends = report_data['trends']
            html += f"""
            <div class="section-title">📈 ANALYSE DES TENDANCES ET PICS</div>
            <p><strong>Tendance générale:</strong> {trends['trend_icon']} {trends['trend']}</p>
            <p><strong>{trends['statistics']['total_peaks']} pic(s) détecté(s)</strong> - Seuil: {trends['statistics']['peak_threshold']} mentions/jour</p>
            
            <div class="chart-container">
                <h4>Graphique temporel des mentions</h4>
                <table>
                    <tr><th>Date</th><th>Mentions</th><th>Positif</th><th>Neutre</th><th>Négatif</th><th>Statut</th></tr>
            """
            
            for day_data in trends['daily_data'][-14:]:  # Derniers 14 jours
                is_peak = any(p['date'] == day_data['date'] for p in trends['peaks'])
                peak_indicator = '<span class="peak-indicator">PIC</span>' if is_peak else ''
                
                html += f"""
                    <tr>
                        <td>{day_data['date_display']}</td>
                        <td><strong>{day_data['mentions']}</strong></td>
                        <td>{day_data['positive']}</td>
                        <td>{day_data['neutral']}</td>
                        <td>{day_data['negative']}</td>
                        <td>{peak_indicator}</td>
                    </tr>
                """
            
            html += "</table></div>"
            
            # Analyse des pics
            if trends['peaks']:
                html += f"""
                <h4>Analyse des pics d'activité</h4>
                <p>{trends['peak_analysis']['summary']}</p>
                <p><strong>Déclencheurs possibles:</strong> {', '.join(trends['peak_analysis']['possible_triggers'][:3])}</p>
                """
        
        html += '<div class="page-break"></div>'
        
        # Page 2: Contenu clé et influences
        if 'key_content' in report_data:
            content = report_data['key_content']
            html += f"""
            <div class="header">
                <h1>💬 CONTENUS ET INFLUENCES CLÉS</h1>
            </div>
            
            <div class="section-title">📋 ARGUMENTS RÉCURRENTS</div>
            <p><strong>Thèmes les plus fréquents:</strong></p>
            <ul>
            """
            
            for theme, count in content['common_themes'][:5]:
                html += f"<li><strong>{theme}</strong> ({count} occurrences)</li>"
            
            html += "</ul>"
            
            # Publications les plus engageantes par sentiment
            for sentiment in ['negative', 'positive']:
                if content['content_by_sentiment'][sentiment]:
                    sentiment_emoji = '😞' if sentiment == 'negative' else '😊'
                    html += f"""
                    <h4>{sentiment_emoji} Publications {sentiment}s les plus engageantes</h4>
                    """
                    
                    for pub in content['content_by_sentiment'][sentiment][:3]:
                        html += f"""
                        <div style="background: #f9fafb; padding: 10px; margin: 8px 0; border-radius: 6px;">
                            <p><strong>{pub['title'][:100]}...</strong></p>
                            <p style="font-size: 9pt; color: #666;">{pub['content'][:200]}...</p>
                            <p style="font-size: 8pt; color: #888;">
                                {pub['author']} • {pub['source']} • ⭐ {pub['engagement']} • {pub['published_at']}
                            </p>
                        </div>
                        """
        
        html += '<div class="page-break"></div>'
        
        # Page 3: Profils détaillés des influenceurs
        if 'detailed_influencers' in report_data:
            influencers = report_data['detailed_influencers']
            html += f"""
            <div class="header">
                <h1>👑 PROFILS DÉTAILLÉS DES INFLUENCEURS</h1>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{influencers['summary']['total_active']}</div>
                    <div class="metric-label">Influenceurs actifs</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{influencers['summary']['high_risk']}</div>
                    <div class="metric-label">À risque élevé</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{influencers['summary']['declining_tone']}</div>
                    <div class="metric-label">Ton en dégradation</div>
                </div>
            </div>
            
            <table>
                <tr>
                    <th>Influenceur</th>
                    <th>Source</th>
                    <th>Portée estimée</th>
                    <th>Engagement</th>
                    <th>Évolution ton</th>
                    <th>Risque</th>
                    <th>Freq. pub.</th>
                </tr>
            """
            
            for inf in influencers['influencers'][:12]:
                risk_color = '#ef4444' if inf['risk_level'] == 'ÉLEVÉ' else '#f59e0b' if inf['risk_level'] == 'MODÉRÉ' else '#10b981'
                tone_arrow = '↗️' if inf['tone_evolution'] > 0.1 else '↘️' if inf['tone_evolution'] < -0.1 else '➡️'
                
                html += f"""
                    <tr>
                        <td><strong>{inf['author'][:20]}</strong></td>
                        <td>{inf['source'].upper()}</td>
                        <td>{inf['estimated_followers']}</td>
                        <td>{inf['total_engagement']:.0f}</td>
                        <td>{tone_arrow} {inf['tone_evolution']:+.2f}</td>
                        <td style="color: {risk_color};"><strong>{inf['risk_level']}</strong></td>
                        <td>{inf['posting_frequency']:.1f}/j</td>
                    </tr>
                """
            
            html += "</table>"
        
        html += '<div class="page-break"></div>'
        
        # Page 4: Géographie et comparaison
        if 'geography' in report_data or 'comparison' in report_data:
            html += f"""
            <div class="header">
                <h1>🌍 ANALYSE GÉOGRAPHIQUE ET COMPARATIVE</h1>
            </div>
            """
            
            # Géographie
            if 'geography' in report_data:
                geo = report_data['geography']
                html += f"""
                <div class="section-title">🗺️ RÉPARTITION GÉOGRAPHIQUE</div>
                <p><strong>{geo['total_countries']} pays actifs</strong> - Concentration sur top 3: {geo['concentration_ratio']}%</p>
                
                <table>
                    <tr><th>Pays</th><th>Mentions</th><th>% Total</th><th>Risque</th></tr>
                """
                
                for country in geo['top_countries'][:8]:
                    risk_info = next((r for r in geo['risk_countries'] if r['country'] == country['country_name']), None)
                    risk_text = f"⚠️ {risk_info['negative_ratio']:.0f}% négatif" if risk_info else "✅ Normal"
                    
                    html += f"""
                        <tr>
                            <td><strong>{country['country_name']}</strong></td>
                            <td>{country['mention_count']}</td>
                            <td>{country['percentage']:.1f}%</td>
                            <td>{risk_text}</td>
                        </tr>
                    """
                
                html += "</table>"
            
            # Comparaison temporelle
            if 'comparison' in report_data:
                comp = report_data['comparison']
                html += f"""
                <div class="section-title">📊 COMPARAISON AVEC PÉRIODE PRÉCÉDENTE</div>
                <p><strong>Interprétation:</strong> {comp['interpretation']}</p>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value" style="color: {'#ef4444' if comp['changes']['volume'] < 0 else '#10b981'}">{comp['changes']['volume']:+.1f}%</div>
                        <div class="metric-label">Évolution volume</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" style="color: {'#ef4444' if comp['changes']['sentiment'] > 0 else '#10b981'}">{comp['changes']['sentiment']:+.1f}pts</div>
                        <div class="metric-label">Évolution sentiment</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" style="color: {'#ef4444' if comp['changes']['engagement'] < 0 else '#10b981'}">{comp['changes']['engagement']:+.1f}%</div>
                        <div class="metric-label">Évolution engagement</div>
                    </div>
                </div>
                
                <p><strong>Nouvelles sources:</strong> {', '.join(comp['sources_evolution']['new_sources']) if comp['sources_evolution']['new_sources'] else 'Aucune'}</p>
                <p><strong>Sources perdues:</strong> {', '.join(comp['sources_evolution']['lost_sources']) if comp['sources_evolution']['lost_sources'] else 'Aucune'}</p>
                """
        
        html += '<div class="page-break"></div>'
        
        # Page 5: Recommandations opérationnelles
        if 'recommendations' in report_data:
            recs = report_data['recommendations']
            html += f"""
            <div class="header">
                <h1>🎯 RECOMMANDATIONS OPÉRATIONNELLES</h1>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{recs['summary']['urgent']}</div>
                    <div class="metric-label">Urgent</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{recs['summary']['high']}</div>
                    <div class="metric-label">Priorité haute</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{recs['summary']['medium']}</div>
                    <div class="metric-label">Priorité moyenne</div>
                </div>
            </div>
            """
            
            for rec in recs['recommendations']:
                priority_color = '#ef4444' if rec['priority'] == 1 else '#f59e0b' if rec['priority'] == 2 else '#10b981'
                
                html += f"""
                <div class="recommendation" style="border-color: {priority_color};">
                    <div class="recommendation-title">{rec['icon']} {rec['title']} ({rec['category']})</div>
                    <p>{rec['description']}</p>
                    <ul>
                """
                
                for action in rec['actions']:
                    html += f"<li>{action}</li>"
                
                html += "</ul></div>"
        
        html += """
            <div class="footer">
                Rapport généré par Superviseur MINDEF | Confidentiel - Usage interne uniquement
            </div>
        </body>
        </html>
        """
        
        return html

    def generate_enhanced_pdf(self, report_data: Dict) -> bytes:
        """
        Générer le PDF du rapport enrichi
        """
        try:
            from weasyprint import HTML
            
            html_content = self.generate_enhanced_html_report(report_data)
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            return pdf_bytes
            
        except ImportError:
            logger.warning("WeasyPrint not available, generating HTML only")
            html_content = self.generate_enhanced_html_report(report_data)
            return html_content.encode('utf-8')