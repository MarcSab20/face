"""
Générateur de Rapports Intelligents avec IA Souveraine
Génère des rapports complets basés sur l'analyse IA sans dépendance externe
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from collections import Counter
import json
import asyncio
from io import BytesIO

from app.ai_service import IntelligentAnalysisAgent, AnalysisContext
from app.models import Keyword, Mention

logger = logging.getLogger(__name__)


class IntelligentReportGenerator:
    """Générateur de rapports avec IA souveraine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_agent = IntelligentAnalysisAgent()
    
    async def generate_complete_report(
        self,
        keyword_ids: List[int],
        days: int = 30,
        report_title: str = "",
        include_web_analysis: bool = True,
        format_type: str = "pdf"
    ) -> Dict:
        """Générer un rapport complet avec analyse IA"""
        
        # 1. Valider les paramètres
        keywords = self.db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        if not keywords:
            raise ValueError("Aucun mot-clé trouvé")
        
        keyword_names = [kw.keyword for kw in keywords]
        since_date = datetime.utcnow() - timedelta(days=days)
        
        logger.info(f"Génération rapport IA: {len(keywords)} mots-clés, {days} jours")
        
        # 2. Récupérer les données de base
        base_data = await self._collect_base_data(keyword_ids, since_date)
        
        # 3. Préparer le contexte d'analyse
        analysis_context = self._prepare_analysis_context(
            base_data, keyword_names, days
        )
        
        # 4. Lancer l'analyse IA
        ai_analysis = await self.ai_agent.generate_intelligent_report(
            analysis_context, 
            self.db if include_web_analysis else None
        )
        
        # 5. Compiler le rapport final
        report_data = {
            'metadata': {
                'title': report_title or f"Rapport IA - {', '.join(keyword_names)}",
                'keywords': keyword_names,
                'keyword_ids': keyword_ids,
                'period_days': days,
                'generated_at': datetime.utcnow(),
                'include_web_analysis': include_web_analysis,
                'format': format_type
            },
            'summary': {
                'total_mentions': len(base_data['mentions']),
                'sources_count': len(base_data['sources_distribution']),
                'period_analyzed': f"{days} jours",
                'web_content_analyzed': len(analysis_context.web_content) if analysis_context.web_content else 0
            },
            'base_data': base_data,
            'ai_analysis': ai_analysis,
            'visualizations': self._prepare_visualizations(base_data, ai_analysis),
            'actionable_insights': self._extract_actionable_insights(ai_analysis),
            'executive_summary': self._generate_executive_summary(base_data, ai_analysis)
        }
        
        logger.info("Rapport IA généré avec succès")
        return report_data
    
    async def _collect_base_data(self, keyword_ids: List[int], since_date: datetime) -> Dict:
        """Collecter les données de base depuis la base de données"""
        
        # Récupérer toutes les mentions
        mentions_query = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).order_by(desc(Mention.published_at))
        
        mentions = mentions_query.all()
        
        # Convertir en dictionnaires pour l'IA
        mentions_data = []
        for mention in mentions:
            mentions_data.append({
                'id': mention.id,
                'title': mention.title,
                'content': mention.content,
                'author': mention.author,
                'source': mention.source,
                'source_url': mention.source_url,
                'sentiment': mention.sentiment,
                'engagement_score': mention.engagement_score,
                'published_at': mention.published_at.isoformat() if mention.published_at else None,
                'collected_at': mention.collected_at.isoformat(),
                'metadata': json.loads(mention.mention_metadata) if mention.mention_metadata else {}
            })
        
        # Analyser les distributions
        sentiment_distribution = self._calculate_sentiment_distribution(mentions)
        sources_distribution = self._calculate_sources_distribution(mentions)
        temporal_distribution = self._calculate_temporal_distribution(mentions)
        engagement_stats = self._calculate_engagement_stats(mentions)
        top_authors = self._calculate_top_authors(mentions)
        
        return {
            'mentions': mentions_data,
            'sentiment_distribution': sentiment_distribution,
            'sources_distribution': sources_distribution,
            'temporal_distribution': temporal_distribution,
            'engagement_stats': engagement_stats,
            'top_authors': top_authors,
            'geographic_hints': self._extract_geographic_hints(mentions),
            'content_categories': self._categorize_content(mentions_data)
        }
    
    def _prepare_analysis_context(self, base_data: Dict, keyword_names: List[str], days: int) -> AnalysisContext:
        """Préparer le contexte pour l'analyse IA"""
        
        # Préparer les données temporelles
        time_trends = []
        for date_str, count in base_data['temporal_distribution'].items():
            time_trends.append({
                'date': date_str,
                'count': count
            })
        
        time_trends.sort(key=lambda x: x['date'])
        
        # Préparer les données d'influenceurs
        influencers_data = []
        for author_data in base_data['top_authors'][:20]:  # Top 20
            sentiment_score = self._calculate_author_sentiment_score(
                author_data['author'], base_data['mentions']
            )
            
            influencers_data.append({
                'author': author_data['author'],
                'source': author_data['main_source'],
                'mention_count': author_data['mentions_count'],
                'total_engagement': author_data['total_engagement'],
                'avg_engagement': author_data['avg_engagement'],
                'sentiment_score': sentiment_score
            })
        
        return AnalysisContext(
            mentions=base_data['mentions'],
            keywords=keyword_names,
            period_days=days,
            total_mentions=len(base_data['mentions']),
            sentiment_distribution=base_data['sentiment_distribution'],
            top_sources=base_data['sources_distribution'],
            engagement_stats=base_data['engagement_stats'],
            geographic_data=[],  # Sera enrichi si nécessaire
            influencers_data=influencers_data,
            time_trends=time_trends,
            web_content=[]  # Sera enrichi par l'IA
        )
    
    def _calculate_sentiment_distribution(self, mentions: List) -> Dict[str, int]:
        """Calculer la distribution des sentiments"""
        distribution = {'positive': 0, 'neutral': 0, 'negative': 0, 'unknown': 0}
        
        for mention in mentions:
            sentiment = mention.sentiment or 'unknown'
            if sentiment in distribution:
                distribution[sentiment] += 1
            else:
                distribution['unknown'] += 1
        
        return distribution
    
    def _calculate_sources_distribution(self, mentions: List) -> Dict[str, int]:
        """Calculer la distribution des sources"""
        return dict(Counter(mention.source for mention in mentions).most_common())
    
    def _calculate_temporal_distribution(self, mentions: List) -> Dict[str, int]:
        """Calculer la distribution temporelle"""
        daily_counts = {}
        
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date().isoformat()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        return daily_counts
    
    def _calculate_engagement_stats(self, mentions: List) -> Dict[str, float]:
        """Calculer les statistiques d'engagement"""
        engagements = [mention.engagement_score for mention in mentions if mention.engagement_score]
        
        if not engagements:
            return {'total': 0, 'average': 0, 'max': 0, 'min': 0}
        
        return {
            'total': sum(engagements),
            'average': sum(engagements) / len(engagements),
            'max': max(engagements),
            'min': min(engagements),
            'count': len(engagements)
        }
    
    def _calculate_top_authors(self, mentions: List) -> List[Dict]:
        """Calculer les top auteurs"""
        author_stats = {}
        
        for mention in mentions:
            author = mention.author
            if author not in author_stats:
                author_stats[author] = {
                    'author': author,
                    'mentions_count': 0,
                    'total_engagement': 0,
                    'sources': set(),
                    'sentiments': []
                }
            
            stats = author_stats[author]
            stats['mentions_count'] += 1
            stats['total_engagement'] += mention.engagement_score
            stats['sources'].add(mention.source)
            if mention.sentiment:
                stats['sentiments'].append(mention.sentiment)
        
        # Formater les résultats
        top_authors = []
        for author, stats in author_stats.items():
            if stats['mentions_count'] >= 2:  # Au moins 2 mentions
                top_authors.append({
                    'author': author,
                    'mentions_count': stats['mentions_count'],
                    'total_engagement': stats['total_engagement'],
                    'avg_engagement': stats['total_engagement'] / stats['mentions_count'],
                    'sources_count': len(stats['sources']),
                    'main_source': list(stats['sources'])[0] if stats['sources'] else 'unknown',
                    'positive_ratio': stats['sentiments'].count('positive') / len(stats['sentiments']) if stats['sentiments'] else 0
                })
        
        # Trier par engagement total
        top_authors.sort(key=lambda x: x['total_engagement'], reverse=True)
        return top_authors
    
    def _calculate_author_sentiment_score(self, author: str, mentions: List[Dict]) -> float:
        """Calculer le score de sentiment pour un auteur"""
        author_mentions = [m for m in mentions if m['author'] == author]
        
        if not author_mentions:
            return 50.0  # Neutre par défaut
        
        sentiments = [m['sentiment'] for m in author_mentions if m['sentiment']]
        
        if not sentiments:
            return 50.0
        
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')
        total_count = len(sentiments)
        
        # Score sur 100 (0 = très négatif, 100 = très positif)
        if total_count == 0:
            return 50.0
        
        positive_ratio = positive_count / total_count
        negative_ratio = negative_count / total_count
        
        # Formule: base 50 + écart positif - écart négatif
        score = 50 + (positive_ratio * 50) - (negative_ratio * 50)
        return max(0, min(100, score))
    
    def _extract_geographic_hints(self, mentions: List) -> List[Dict]:
        """Extraire des indices géographiques du contenu"""
        # Mots-clés géographiques simples
        geo_keywords = {
            'france': 'FR', 'paris': 'FR', 'lyon': 'FR', 'marseille': 'FR',
            'usa': 'US', 'america': 'US', 'new york': 'US', 'california': 'US',
            'uk': 'GB', 'london': 'GB', 'england': 'GB',
            'germany': 'DE', 'berlin': 'DE', 'allemagne': 'DE',
            'canada': 'CA', 'toronto': 'CA', 'montreal': 'CA',
            'japan': 'JP', 'tokyo': 'JP', 'japon': 'JP',
            'china': 'CN', 'beijing': 'CN', 'chine': 'CN'
        }
        
        geo_mentions = {}
        
        for mention in mentions:
            content_lower = f"{mention.title} {mention.content}".lower()
            
            for geo_term, country_code in geo_keywords.items():
                if geo_term in content_lower:
                    if country_code not in geo_mentions:
                        geo_mentions[country_code] = 0
                    geo_mentions[country_code] += 1
        
        # Convertir en liste triée
        geo_data = []
        for country_code, count in sorted(geo_mentions.items(), key=lambda x: x[1], reverse=True):
            geo_data.append({
                'country_code': country_code,
                'mentions_count': count
            })
        
        return geo_data[:10]  # Top 10 pays
    
    def _categorize_content(self, mentions: List[Dict]) -> Dict[str, int]:
        """Catégoriser le contenu par thèmes"""
        categories = {
            'actualité': ['news', 'breaking', 'actualité', 'info', 'journal'],
            'opinion': ['opinion', 'avis', 'pense', 'crois', 'selon moi'],
            'analyse': ['analyse', 'étude', 'rapport', 'recherche', 'data'],
            'promotion': ['promo', 'offre', 'discount', 'solde', 'achat'],
            'service client': ['problème', 'bug', 'aide', 'support', 'sav'],
            'événement': ['événement', 'event', 'conférence', 'salon', 'meeting']
        }
        
        category_counts = {cat: 0 for cat in categories.keys()}
        category_counts['autre'] = 0
        
        for mention in mentions:
            content_lower = f"{mention['title']} {mention['content']}".lower()
            
            categorized = False
            for category, keywords in categories.items():
                if any(keyword in content_lower for keyword in keywords):
                    category_counts[category] += 1
                    categorized = True
                    break
            
            if not categorized:
                category_counts['autre'] += 1
        
        return category_counts
    
    def _prepare_visualizations(self, base_data: Dict, ai_analysis: Dict) -> Dict:
        """Préparer les données de visualisation"""
        
        visualizations = {
            'sentiment_chart': {
                'type': 'pie',
                'data': base_data['sentiment_distribution'],
                'title': 'Distribution des Sentiments'
            },
            'sources_chart': {
                'type': 'bar',
                'data': dict(list(base_data['sources_distribution'].items())[:10]),
                'title': 'Top 10 Sources'
            },
            'timeline_chart': {
                'type': 'line',
                'data': base_data['temporal_distribution'],
                'title': 'Évolution Temporelle'
            },
            'engagement_chart': {
                'type': 'histogram',
                'data': self._prepare_engagement_histogram(base_data['mentions']),
                'title': 'Distribution de l\'Engagement'
            }
        }
        
        # Ajouter les graphiques IA si disponibles
        if 'trends' in ai_analysis:
            trends_data = ai_analysis['trends'].get('patterns', {})
            if trends_data.get('peaks'):
                visualizations['peaks_chart'] = {
                    'type': 'scatter',
                    'data': trends_data['peaks'],
                    'title': 'Pics d\'Activité Détectés'
                }
        
        return visualizations
    
    def _prepare_engagement_histogram(self, mentions: List[Dict]) -> List[Dict]:
        """Préparer l'histogramme d'engagement"""
        engagements = [m['engagement_score'] for m in mentions if m['engagement_score'] > 0]
        
        if not engagements:
            return []
        
        # Créer des bins
        max_engagement = max(engagements)
        bin_size = max_engagement / 10 if max_engagement > 0 else 1
        
        bins = []
        for i in range(10):
            min_val = i * bin_size
            max_val = (i + 1) * bin_size
            count = sum(1 for eng in engagements if min_val <= eng < max_val)
            
            bins.append({
                'range': f"{int(min_val)}-{int(max_val)}",
                'count': count
            })
        
        return bins
    
    def _extract_actionable_insights(self, ai_analysis: Dict) -> List[Dict]:
        """Extraire les insights actionnables de l'analyse IA"""
        insights = []
        
        # Insights de sentiment
        if 'sentiment' in ai_analysis:
            sentiment_insights = ai_analysis['sentiment'].get('insights', [])
            for insight in sentiment_insights:
                insights.append({
                    'category': 'sentiment',
                    'priority': 'high' if 'critique' in insight.lower() else 'medium',
                    'message': insight,
                    'action': self._suggest_action_for_sentiment_insight(insight)
                })
        
        # Insights d'influenceurs
        if 'influencers' in ai_analysis:
            risk_assessment = ai_analysis['influencers'].get('risk_assessment', {})
            high_risk_count = len(risk_assessment.get('high_risk', []))
            if high_risk_count > 0:
                insights.append({
                    'category': 'influencers',
                    'priority': 'critical',
                    'message': f"{high_risk_count} influenceur(s) à risque élevé identifié(s)",
                    'action': 'Engagement immédiat nécessaire avec ces comptes'
                })
        
        # Insights de tendances
        if 'trends' in ai_analysis:
            patterns = ai_analysis['trends'].get('patterns', {})
            peaks_count = patterns.get('peaks_detected', 0)
            if peaks_count > 2:
                insights.append({
                    'category': 'trends',
                    'priority': 'medium',
                    'message': f"{peaks_count} pics d'activité détectés",
                    'action': 'Analyser les causes des pics pour anticipation future'
                })
        
        # Insights de contenu web
        if 'web_content' in ai_analysis:
            engagement_analysis = ai_analysis['web_content'].get('engagement_analysis', {})
            if engagement_analysis.get('engagement_rate', 0) < 0.3:
                insights.append({
                    'category': 'web_content',
                    'priority': 'medium',
                    'message': 'Taux d\'engagement web faible détecté',
                    'action': 'Optimiser la stratégie de contenu pour plus d\'interaction'
                })
        
        return insights[:10]  # Limiter à 10 insights
    
    def _suggest_action_for_sentiment_insight(self, insight: str) -> str:
        """Suggérer une action basée sur un insight de sentiment"""
        insight_lower = insight.lower()
        
        if 'critique' in insight_lower or 'crise' in insight_lower:
            return 'Activation protocole de gestion de crise'
        elif 'négatif' in insight_lower:
            return 'Préparation de stratégie de correction d\'image'
        elif 'positif' in insight_lower and 'opportunité' in insight_lower:
            return 'Capitaliser sur le sentiment positif avec campagne ciblée'
        elif 'polarisé' in insight_lower:
            return 'Communication équilibrée pour réconcilier les opinions'
        else:
            return 'Surveillance continue et analyse approfondie'
    
    def _generate_executive_summary(self, base_data: Dict, ai_analysis: Dict) -> Dict:
        """Générer un résumé exécutif"""
        
        # Extraire les éléments clés
        total_mentions = len(base_data['mentions'])
        
        # Sentiment dominant
        sentiment_dist = base_data['sentiment_distribution']
        total_sentiment = sum(sentiment_dist.values())
        
        if total_sentiment > 0:
            sentiment_percentages = {
                k: (v / total_sentiment) * 100 
                for k, v in sentiment_dist.items()
            }
            
            dominant_sentiment = max(sentiment_percentages, key=sentiment_percentages.get)
            dominant_percentage = sentiment_percentages[dominant_sentiment]
        else:
            dominant_sentiment = 'unknown'
            dominant_percentage = 0
        
        # Niveau de priorité de l'IA
        ai_priority = ai_analysis.get('synthesis', {}).get('priority_level', 'NORMAL')
        
        # Top source
        top_source = max(base_data['sources_distribution'], key=base_data['sources_distribution'].get) if base_data['sources_distribution'] else 'unknown'
        
        # Engagement moyen
        avg_engagement = base_data['engagement_stats'].get('average', 0)
        
        # Construire le résumé
        summary = {
            'key_figures': {
                'total_mentions': total_mentions,
                'dominant_sentiment': f"{dominant_sentiment} ({dominant_percentage:.0f}%)",
                'top_source': top_source,
                'avg_engagement': round(avg_engagement, 1),
                'ai_priority_level': ai_priority
            },
            'main_findings': self._extract_main_findings(ai_analysis),
            'critical_points': self._extract_critical_points(ai_analysis),
            'next_steps': self._extract_next_steps(ai_analysis),
            'confidence_score': self._calculate_confidence_score(base_data, ai_analysis)
        }
        
        return summary
    
    def _extract_main_findings(self, ai_analysis: Dict) -> List[str]:
        """Extraire les principales découvertes"""
        findings = []
        
        # Findings de sentiment
        sentiment_analysis = ai_analysis.get('sentiment', {}).get('analysis', '')
        if sentiment_analysis:
            # Extraire la première phrase comme finding principal
            first_sentence = sentiment_analysis.split('.')[0]
            if len(first_sentence) > 20:
                findings.append(f"Sentiment: {first_sentence}")
        
        # Findings de tendances
        trends_analysis = ai_analysis.get('trends', {}).get('analysis', '')
        if trends_analysis:
            first_sentence = trends_analysis.split('.')[0]
            if len(first_sentence) > 20:
                findings.append(f"Tendances: {first_sentence}")
        
        # Findings d'influenceurs
        influencers_analysis = ai_analysis.get('influencers', {})
        if influencers_analysis.get('top_influencers'):
            top_count = len(influencers_analysis['top_influencers'])
            findings.append(f"Influenceurs: {top_count} comptes influents identifiés")
        
        # Findings de contenu web
        web_analysis = ai_analysis.get('web_content', {})
        if web_analysis.get('articles_count', 0) > 0:
            articles_count = web_analysis['articles_count']
            comments_count = web_analysis.get('comments_count', 0)
            findings.append(f"Contenu web: {articles_count} articles analysés, {comments_count} commentaires extraits")
        
        return findings[:5]  # Top 5 findings
    
    def _extract_critical_points(self, ai_analysis: Dict) -> List[str]:
        """Extraire les points critiques"""
        critical_points = []
        
        # Points critiques basés sur la priorité
        priority = ai_analysis.get('synthesis', {}).get('priority_level', 'NORMAL')
        
        if priority == 'CRITIQUE':
            critical_points.append("🚨 NIVEAU CRITIQUE: Intervention immédiate requise")
        elif priority == 'ÉLEVÉ':
            critical_points.append("⚠️ NIVEAU ÉLEVÉ: Surveillance renforcée nécessaire")
        
        # Points critiques des influenceurs
        influencer_risks = ai_analysis.get('influencers', {}).get('risk_assessment', {})
        high_risk_influencers = influencer_risks.get('high_risk', [])
        if high_risk_influencers:
            critical_points.append(
                f"👑 INFLUENCEURS À RISQUE: {len(high_risk_influencers)} compte(s) critique(s)"
            )
        
        # Points critiques du contenu web
        web_analysis = ai_analysis.get('web_content', {})
        engagement_analysis = web_analysis.get('engagement_analysis', {})
        if engagement_analysis.get('engagement_rate', 1) < 0.2:
            critical_points.append("📉 ENGAGEMENT FAIBLE: Réactivité du public préoccupante")
        
        # Points critiques des tendances
        trends_patterns = ai_analysis.get('trends', {}).get('patterns', {})
        if trends_patterns.get('peaks_detected', 0) > 3:
            critical_points.append("📈 VOLATILITÉ ÉLEVÉE: Activité très irrégulière détectée")
        
        return critical_points[:5]  # Top 5 points critiques
    
    def _extract_next_steps(self, ai_analysis: Dict) -> List[str]:
        """Extraire les prochaines étapes recommandées"""
        next_steps = []
        
        # Étapes basées sur les recommandations IA
        recommendations = ai_analysis.get('recommendations', {})
        if recommendations.get('urgent_actions'):
            next_steps.extend(recommendations['urgent_actions'][:3])
        
        # Étapes génériques basées sur la priorité
        priority = ai_analysis.get('synthesis', {}).get('priority_level', 'NORMAL')
        
        if priority in ['CRITIQUE', 'ÉLEVÉ']:
            next_steps.append("Mise en place monitoring H24")
            next_steps.append("Préparation éléments de communication")
        
        # Étapes basées sur l'analyse web
        web_analysis = ai_analysis.get('web_content', {})
        if web_analysis.get('articles_count', 0) > 0:
            next_steps.append("Suivi des nouveaux articles et commentaires")
        
        # Si pas d'étapes spécifiques, ajouter des étapes génériques
        if not next_steps:
            next_steps.extend([
                "Continuer la surveillance habituelle",
                "Analyser l'évolution sur 24-48h",
                "Préparer points de vigilance"
            ])
        
        return next_steps[:5]  # Top 5 étapes
    
    def _calculate_confidence_score(self, base_data: Dict, ai_analysis: Dict) -> float:
        """Calculer un score de confiance pour l'analyse"""
        confidence_factors = []
        
        # Facteur 1: Volume de données
        mentions_count = len(base_data['mentions'])
        if mentions_count >= 100:
            confidence_factors.append(0.9)
        elif mentions_count >= 50:
            confidence_factors.append(0.7)
        elif mentions_count >= 20:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.3)
        
        # Facteur 2: Diversité des sources
        sources_count = len(base_data['sources_distribution'])
        if sources_count >= 5:
            confidence_factors.append(0.8)
        elif sources_count >= 3:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)
        
        # Facteur 3: Période d'analyse
        # (supposé correct car géré en amont)
        confidence_factors.append(0.7)
        
        # Facteur 4: Analyse web disponible
        web_analysis = ai_analysis.get('web_content', {})
        if web_analysis.get('articles_count', 0) > 0:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)
        
        # Facteur 5: Qualité des données de sentiment
        sentiment_dist = base_data['sentiment_distribution']
        total_sentiment = sum(sentiment_dist.values())
        unknown_ratio = sentiment_dist.get('unknown', 0) / max(total_sentiment, 1)
        
        if unknown_ratio < 0.2:
            confidence_factors.append(0.8)
        elif unknown_ratio < 0.5:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)
        
        # Calculer la moyenne
        return sum(confidence_factors) / len(confidence_factors)
    
    async def generate_html_report(self, report_data: Dict) -> str:
        """Générer le rapport au format HTML"""
        
        metadata = report_data['metadata']
        summary = report_data['summary']
        ai_analysis = report_data['ai_analysis']
        executive_summary = report_data['executive_summary']
        
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{metadata['title']}</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{ 
                    background: white; border-radius: 15px; padding: 40px; 
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }}
                .header {{ 
                    text-align: center; padding-bottom: 30px; 
                    border-bottom: 3px solid #667eea; margin-bottom: 30px;
                }}
                .header h1 {{ 
                    color: #667eea; font-size: 2.5em; margin: 0 0 10px 0; 
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                }}
                .ai-badge {{ 
                    background: linear-gradient(45deg, #667eea, #764ba2); 
                    color: white; padding: 8px 16px; border-radius: 20px; 
                    font-size: 0.9em; font-weight: bold; margin: 0 10px;
                    display: inline-block;
                }}
                .section {{ margin: 30px 0; }}
                .section-title {{ 
                    color: #667eea; font-size: 1.5em; font-weight: bold; 
                    margin: 20px 0 15px 0; padding-bottom: 8px; 
                    border-bottom: 2px solid #e5e7eb;
                }}
                .ai-section {{ 
                    background: linear-gradient(135deg, #667eea15, #764ba205); 
                    border-left: 5px solid #667eea; padding: 20px; margin: 15px 0; 
                    border-radius: 8px;
                }}
                .metrics-grid {{ 
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                    gap: 20px; margin: 20px 0;
                }}
                .metric-card {{ 
                    background: linear-gradient(135deg, #f8fafc, #e2e8f0); 
                    padding: 20px; border-radius: 10px; text-align: center;
                    border: 1px solid #e5e7eb;
                }}
                .metric-value {{ 
                    font-size: 2em; font-weight: bold; color: #667eea; margin: 10px 0;
                }}
                .metric-label {{ 
                    color: #6b7280; font-size: 0.9em; font-weight: 500;
                }}
                .priority-critical {{ 
                    background: #fef2f2; border: 2px solid #dc2626; color: #dc2626;
                }}
                .priority-high {{ 
                    background: #fef3c7; border: 2px solid #f59e0b; color: #f59e0b;
                }}
                .priority-medium {{ 
                    background: #f0f9ff; border: 2px solid #3b82f6; color: #3b82f6;
                }}
                .priority-normal {{ 
                    background: #f0fdf4; border: 2px solid #10b981; color: #10b981;
                }}
                .insight-list {{ list-style: none; padding: 0; }}
                .insight-item {{ 
                    background: #f9fafb; margin: 8px 0; padding: 15px; 
                    border-left: 4px solid #667eea; border-radius: 6px;
                }}
                .finding-item {{
                    background: #f8fafc; margin: 10px 0; padding: 12px;
                    border-radius: 6px; border-left: 3px solid #10b981;
                }}
                .critical-point {{
                    background: #fef2f2; margin: 10px 0; padding: 12px;
                    border-radius: 6px; border-left: 3px solid #ef4444;
                    font-weight: 500;
                }}
                .next-step {{
                    background: #f0f9ff; margin: 8px 0; padding: 10px;
                    border-radius: 6px; border-left: 3px solid #3b82f6;
                }}
                .confidence-bar {{
                    width: 100%; height: 20px; background: #e5e7eb; 
                    border-radius: 10px; overflow: hidden; margin: 10px 0;
                }}
                .confidence-fill {{
                    height: 100%; background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
                    border-radius: 10px; transition: width 0.3s ease;
                }}
                .footer {{ 
                    margin-top: 40px; padding-top: 20px; 
                    border-top: 2px solid #e5e7eb; text-align: center; 
                    color: #6b7280; font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Header -->
                <div class="header">
                    <h1>🤖 {metadata['title']}</h1>
                    <span class="ai-badge">IA SOUVERAINE</span>
                    <span class="ai-badge">ANALYSE INTELLIGENTE</span>
                    <p style="color: #6b7280; margin-top: 15px;">
                        Généré le {metadata['generated_at'].strftime('%d/%m/%Y à %H:%M')} • 
                        Période: {metadata['period_days']} jours • 
                        Mots-clés: {', '.join(metadata['keywords'])}
                    </p>
                </div>
                
                <!-- Résumé Exécutif -->
                <div class="section">
                    <h2 class="section-title">📊 Résumé Exécutif</h2>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{summary['total_mentions']}</div>
                            <div class="metric-label">Total Mentions</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{executive_summary['key_figures']['dominant_sentiment']}</div>
                            <div class="metric-label">Sentiment Dominant</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{executive_summary['key_figures']['top_source']}</div>
                            <div class="metric-label">Source Principale</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{executive_summary['key_figures']['avg_engagement']}</div>
                            <div class="metric-label">Engagement Moyen</div>
                        </div>
                    </div>
                    
                    <div class="ai-section priority-{executive_summary['key_figures']['ai_priority_level'].lower()}">
                        <h3>🎯 Niveau de Priorité IA: {executive_summary['key_figures']['ai_priority_level']}</h3>
                        <div style="margin-top: 15px;">
                            <strong>Score de Confiance:</strong>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: {executive_summary['confidence_score']*100:.0f}%;"></div>
                            </div>
                            {executive_summary['confidence_score']*100:.0f}% de confiance dans l'analyse
                        </div>
                    </div>
                </div>
        """
        
        # Principales découvertes
        if executive_summary.get('main_findings'):
            html += """
                <div class="section">
                    <h2 class="section-title">🔍 Principales Découvertes</h2>
            """
            for finding in executive_summary['main_findings']:
                html += f'<div class="finding-item">{finding}</div>'
            html += "</div>"
        
        # Points critiques
        if executive_summary.get('critical_points'):
            html += """
                <div class="section">
                    <h2 class="section-title">🚨 Points Critiques</h2>
            """
            for point in executive_summary['critical_points']:
                html += f'<div class="critical-point">{point}</div>'
            html += "</div>"
        
        # Analyses IA
        html += """
            <div class="section">
                <h2 class="section-title">🧠 Analyses IA Détaillées</h2>
        """
        
        for analysis_type, analysis_data in ai_analysis.items():
            if isinstance(analysis_data, dict) and 'analysis' in analysis_data:
                type_name = analysis_type.replace('_', ' ').title()
                analysis_text = analysis_data['analysis']
                
                html += f"""
                    <div class="ai-section">
                        <h3>🤖 {type_name}</h3>
                        <p>{analysis_text}</p>
                    </div>
                """
        
        # Prochaines étapes
        if executive_summary.get('next_steps'):
            html += """
                <div class="section">
                    <h2 class="section-title">➡️ Prochaines Étapes Recommandées</h2>
            """
            for i, step in enumerate(executive_summary['next_steps'], 1):
                html += f'<div class="next-step">{i}. {step}</div>'
            html += "</div>"
        
        # Insights actionnables
        actionable_insights = report_data.get('actionable_insights', [])
        if actionable_insights:
            html += """
                <div class="section">
                    <h2 class="section-title">💡 Insights Actionnables</h2>
                    <ul class="insight-list">
            """
            for insight in actionable_insights:
                priority_class = f"priority-{insight['priority']}"
                html += f"""
                    <li class="insight-item {priority_class}">
                        <strong>[{insight['category'].upper()}]</strong> {insight['message']}<br>
                        <em>Action suggérée: {insight['action']}</em>
                    </li>
                """
            html += "</ul></div>"
        
        # Footer
        html += f"""
                <div class="footer">
                    <p>🤖 Rapport généré par IA Souveraine • Brand Monitor Intelligence</p>
                    <p>Analyse basée sur {summary['total_mentions']} mentions • 
                       {summary['sources_count']} sources • 
                       {summary.get('web_content_analyzed', 0)} contenus web analysés</p>
                    <p style="font-size: 0.8em; margin-top: 10px;">
                        Technologies: Ollama + HuggingFace Transformers • 
                        Extraction Web Intelligente • Analyse Multi-Agents
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def generate_pdf_report(self, report_data: Dict) -> bytes:
        """Générer le rapport au format PDF"""
        try:
            from weasyprint import HTML, CSS
            
            # Générer le HTML
            html_content = await self.generate_html_report(report_data)
            
            # CSS pour PDF
            pdf_css = CSS(string="""
                @page {
                    size: A4;
                    margin: 1cm;
                }
                body {
                    background: white !important;
                    font-size: 10pt;
                }
                .container {
                    box-shadow: none !important;
                }
            """)
            
            # Générer le PDF
            pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[pdf_css])
            
            return pdf_bytes
            
        except ImportError:
            logger.warning("WeasyPrint non disponible, retour HTML")
            html_content = await self.generate_html_report(report_data)
            return html_content.encode('utf-8')
        except Exception as e:
            logger.error(f"Erreur génération PDF: {e}")
            # Fallback vers HTML
            html_content = await self.generate_html_report(report_data)
            return html_content.encode('utf-8')