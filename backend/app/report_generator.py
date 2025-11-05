"""
Générateur de rapports intelligents avec IA
Utilise les agents IA pour analyser le contenu web et générer des insights avancés
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from collections import Counter
import asyncio

from enhanced_ai_service import ReportIntelligenceAgent, AnalysisContext, WebContent
from app.models import Keyword, Mention

logger = logging.getLogger(__name__)


class IntelligentReportGenerator:
    """Générateur de rapports intelligent avec IA et analyse web"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_agent = ReportIntelligenceAgent()
    
    async def generate_intelligent_report(
        self,
        keyword_ids: List[int],
        days: int = 30,
        report_object: str = "",
        include_web_analysis: bool = True
    ) -> Dict:
        """Générer un rapport enrichi avec analyse IA avancée"""
        
        keywords = self.db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        if not keywords:
            raise ValueError("Aucun mot-clé trouvé")
        
        keywords_names = [kw.keyword for kw in keywords]
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Récupérer toutes les mentions
        mentions = self.db.query(Mention).filter(
            Mention.keyword_id.in_(keyword_ids),
            Mention.published_at >= since_date
        ).order_by(desc(Mention.published_at)).all()
        
        # Préparer le contexte d'analyse pour l'IA
        analysis_context = self._prepare_analysis_context(mentions, keywords_names, days)
        
        # Générer l'analyse IA avec enrichissement web
        ai_analysis = await self.ai_agent.generate_intelligent_analysis(
            analysis_context, 
            self.db if include_web_analysis else None
        )
        
        # Préparer les données du rapport
        report_data = {
            'keywords': keywords_names,
            'keyword_ids': keyword_ids,
            'period_days': days,
            'report_object': report_object or ', '.join(keywords_names),
            'generated_at': datetime.utcnow(),
            'total_mentions': len(mentions),
            'ai_analysis': ai_analysis,  # Analyse IA complète
            'web_content_analyzed': len(analysis_context.web_content) if hasattr(analysis_context, 'web_content') else 0,
        }
        
        # Analyses traditionnelles enrichies avec l'IA
        positive_mentions = [m for m in mentions if m.sentiment == 'positive']
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        neutral_mentions = [m for m in mentions if m.sentiment == 'neutral']
        
        report_data['smart_analysis'] = self._generate_smart_analysis(mentions, days, ai_analysis)
        report_data['engagement_insights'] = self._analyze_engagement_patterns(mentions, ai_analysis)
        report_data['authenticity_assessment'] = self._assess_content_authenticity(ai_analysis)
        report_data['actionable_recommendations'] = self._generate_actionable_recommendations(ai_analysis, mentions)
        report_data['risk_assessment'] = self._generate_enhanced_risk_assessment(mentions, days, ai_analysis)
        report_data['web_insights'] = self._extract_web_insights(ai_analysis)
        
        return report_data
    
    def _prepare_analysis_context(self, mentions: List, keywords: List[str], days: int) -> AnalysisContext:
        """Prépare le contexte pour l'analyse IA"""
        
        # Convertir les mentions en dictionnaires
        mentions_data = []
        for m in mentions:
            mentions_data.append({
                'title': m.title,
                'content': m.content,
                'sentiment': m.sentiment,
                'source': m.source,
                'source_url': m.source_url,
                'author': m.author,
                'engagement_score': m.engagement_score,
                'published_at': m.published_at.isoformat() if m.published_at else None
            })
        
        # Calculer la distribution des sentiments
        sentiment_dist = {'positive': 0, 'neutral': 0, 'negative': 0}
        for m in mentions:
            if m.sentiment:
                sentiment_dist[m.sentiment] = sentiment_dist.get(m.sentiment, 0) + 1
        
        # Statistiques par source
        source_counts = Counter([m.source for m in mentions])
        
        # Statistiques d'engagement
        engagement_scores = [m.engagement_score for m in mentions]
        engagement_stats = {
            'total': sum(engagement_scores),
            'average': sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0,
            'max': max(engagement_scores) if engagement_scores else 0
        }
        
        # Données temporelles
        timeline = {}
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date()
                timeline[date_key] = timeline.get(date_key, 0) + 1
        
        time_trends = [
            {'date': str(date), 'count': count}
            for date, count in sorted(timeline.items())
        ]
        
        # Données d'influenceurs
        influencers_data = []
        author_stats = {}
        for mention in mentions:
            author = mention.author
            if author not in author_stats:
                author_stats[author] = {
                    'author': author,
                    'source': mention.source,
                    'mention_count': 0,
                    'total_engagement': 0,
                    'sentiments': []
                }
            
            author_stats[author]['mention_count'] += 1
            author_stats[author]['total_engagement'] += mention.engagement_score
            if mention.sentiment:
                author_stats[author]['sentiments'].append(mention.sentiment)
        
        for author, stats in author_stats.items():
            sentiments = stats['sentiments']
            positive_ratio = sentiments.count('positive') / len(sentiments) if sentiments else 0
            
            influencers_data.append({
                'author': author,
                'source': stats['source'],
                'mention_count': stats['mention_count'],
                'total_engagement': stats['total_engagement'],
                'sentiment_score': positive_ratio * 100,
                'avg_engagement': stats['total_engagement'] / stats['mention_count']
            })
        
        # Trier par engagement total
        influencers_data.sort(key=lambda x: x['total_engagement'], reverse=True)
        
        return AnalysisContext(
            mentions=mentions_data,
            keywords=keywords,
            period_days=days,
            total_mentions=len(mentions),
            sentiment_distribution=sentiment_dist,
            top_sources=dict(source_counts.most_common(5)),
            engagement_stats=engagement_stats,
            geographic_data=[],  # À implémenter selon vos besoins
            influencers_data=influencers_data,
            time_trends=time_trends,
            web_content=[]  # Sera rempli par l'agent IA
        )
    
    def _generate_smart_analysis(self, mentions: List, days: int, ai_analysis: Dict) -> Dict:
        """Générer une analyse intelligente basée sur l'IA"""
        
        # Extraire les insights IA
        sentiment_insights = ai_analysis.get('sentiment', {}).get('analysis', '')
        trend_insights = ai_analysis.get('trends', {}).get('analysis', '')
        influencer_insights = ai_analysis.get('influencers', {}).get('analysis', '')
        web_insights = ai_analysis.get('web_content', {}).get('analysis', '')
        
        # Calculer des métriques intelligentes
        total_mentions = len(mentions)
        avg_engagement = sum(m.engagement_score for m in mentions) / total_mentions if total_mentions > 0 else 0
        
        # Score de viralité
        high_engagement_mentions = [m for m in mentions if m.engagement_score > avg_engagement * 2]
        virality_score = len(high_engagement_mentions) / total_mentions if total_mentions > 0 else 0
        
        # Score de diversité des sources
        unique_sources = len(set(m.source for m in mentions))
        diversity_score = min(unique_sources / 5, 1.0)  # Normaliser sur 5 sources
        
        return {
            'summary': f"Analyse de {total_mentions} mentions sur {days} jours avec insights IA avancés",
            'key_insights': [
                sentiment_insights[:100] + "..." if len(sentiment_insights) > 100 else sentiment_insights,
                trend_insights[:100] + "..." if len(trend_insights) > 100 else trend_insights,
                influencer_insights[:100] + "..." if len(influencer_insights) > 100 else influencer_insights
            ],
            'web_context': web_insights[:200] + "..." if len(web_insights) > 200 else web_insights,
            'intelligence_metrics': {
                'virality_score': round(virality_score, 3),
                'diversity_score': round(diversity_score, 3),
                'avg_engagement': round(avg_engagement, 2),
                'ai_confidence': ai_analysis.get('executive_summary', {}).get('key_metrics', {}).get('analysis_confidence', 0.0)
            }
        }
    
    def _analyze_engagement_patterns(self, mentions: List, ai_analysis: Dict) -> Dict:
        """Analyser les patterns d'engagement avec l'IA"""
        
        if not mentions:
            return {'pattern': 'Aucune donnée', 'insights': []}
        
        # Analyser la distribution temporelle de l'engagement
        daily_engagement = {}
        for mention in mentions:
            if mention.published_at:
                date_key = mention.published_at.date()
                if date_key not in daily_engagement:
                    daily_engagement[date_key] = {'count': 0, 'total_engagement': 0}
                daily_engagement[date_key]['count'] += 1
                daily_engagement[date_key]['total_engagement'] += mention.engagement_score
        
        # Calculer les moyennes quotidiennes
        daily_averages = []
        for date, data in daily_engagement.items():
            avg_engagement = data['total_engagement'] / data['count'] if data['count'] > 0 else 0
            daily_averages.append({
                'date': str(date),
                'avg_engagement': avg_engagement,
                'mention_count': data['count']
            })
        
        # Identifier les pics d'engagement
        if daily_averages:
            avg_global = sum(d['avg_engagement'] for d in daily_averages) / len(daily_averages)
            peaks = [d for d in daily_averages if d['avg_engagement'] > avg_global * 1.5]
        else:
            peaks = []
        
        # Extraire les insights IA sur l'engagement
        web_engagement = ai_analysis.get('web_content', {}).get('engagement_patterns', {})
        
        return {
            'pattern': 'Variable' if len(peaks) > 2 else 'Stable',
            'daily_averages': daily_averages[-7:],  # 7 derniers jours
            'engagement_peaks': peaks,
            'web_engagement_rate': web_engagement.get('engagement_rate', 0),
            'authenticity_indicators': {
                'web_authenticity': ai_analysis.get('web_content', {}).get('authenticity_score', 0),
                'comment_quality': 'High' if web_engagement.get('comments_with_likes', 0) > 0 else 'Low'
            },
            'insights': [
                f"Pics d'engagement détectés: {len(peaks)} jours",
                f"Taux d'engagement web: {web_engagement.get('engagement_rate', 0):.1%}",
                f"Authenticité estimée: {ai_analysis.get('web_content', {}).get('authenticity_score', 0):.1f}/1.0"
            ]
        }
    
    def _assess_content_authenticity(self, ai_analysis: Dict) -> Dict:
        """Évaluer l'authenticité du contenu avec l'IA"""
        
        # Récupérer les analyses d'authenticité de l'IA
        web_analysis = ai_analysis.get('web_content', {})
        sentiment_analysis = ai_analysis.get('sentiment', {})
        
        authenticity_score = web_analysis.get('authenticity_score', 0.5)
        
        # Déterminer le niveau d'authenticité
        if authenticity_score >= 0.8:
            authenticity_level = "ÉLEVÉE"
            color = "#10b981"
        elif authenticity_score >= 0.6:
            authenticity_level = "MODÉRÉE"
            color = "#f59e0b"
        else:
            authenticity_level = "FAIBLE"
            color = "#ef4444"
        
        # Indicateurs d'authenticité
        indicators = []
        
        if web_analysis.get('comment_insights', {}).get('unique_authors', 0) > 0:
            unique_ratio = web_analysis['comment_insights']['unique_authors'] / max(web_analysis['comment_insights'].get('total_comments', 1), 1)
            indicators.append(f"Diversité des commentateurs: {unique_ratio:.1%}")
        
        if 'web_vs_mentions' in sentiment_analysis:
            alignment = sentiment_analysis['web_vs_mentions'].get('alignment', 'Unknown')
            indicators.append(f"Cohérence sentiment mentions/web: {alignment}")
        
        web_engagement = web_analysis.get('engagement_patterns', {})
        if web_engagement.get('total_comments', 0) > 0:
            indicators.append(f"Engagement réel détecté: {web_engagement['total_comments']} commentaires")
        
        return {
            'authenticity_level': authenticity_level,
            'authenticity_score': round(authenticity_score, 2),
            'color': color,
            'indicators': indicators,
            'red_flags': self._detect_red_flags(ai_analysis),
            'confidence': 'High' if len(indicators) >= 3 else 'Medium' if len(indicators) >= 2 else 'Low'
        }
    
    def _detect_red_flags(self, ai_analysis: Dict) -> List[str]:
        """Détecter les signaux d'alarme d'inauthenticité"""
        red_flags = []
        
        web_analysis = ai_analysis.get('web_content', {})
        
        # Authenticité faible
        if web_analysis.get('authenticity_score', 1.0) < 0.5:
            red_flags.append("Score d'authenticité faible détecté par l'IA")
        
        # Peu de commentaires uniques
        comment_insights = web_analysis.get('comment_insights', {})
        if comment_insights.get('total_comments', 0) > 0:
            unique_ratio = comment_insights.get('unique_authors', 0) / comment_insights['total_comments']
            if unique_ratio < 0.7:
                red_flags.append("Faible diversité des commentateurs")
        
        # Divergence sentiment mentions/web
        sentiment_analysis = ai_analysis.get('sentiment', {})
        if sentiment_analysis.get('web_vs_mentions', {}).get('alignment') == 'Divergent':
            red_flags.append("Divergence entre sentiment officiel et réactions publiques")
        
        return red_flags
    
    def _generate_actionable_recommendations(self, ai_analysis: Dict, mentions: List) -> Dict:
        """Générer des recommandations actionnables basées sur l'IA"""
        
        recommendations = {
            'immediate': [],
            'short_term': [],
            'long_term': []
        }
        
        # Recommandations basées sur les insights IA
        sentiment_insights = ai_analysis.get('sentiment', {}).get('key_insights', [])
        influencer_analysis = ai_analysis.get('influencers', {})
        web_analysis = ai_analysis.get('web_content', {})
        
        # Recommandations immédiates
        executive_summary = ai_analysis.get('executive_summary', {})
        if executive_summary.get('priority_level') == 'CRITIQUE':
            recommendations['immediate'].append({
                'action': '🚨 Activation de la cellule de crise',
                'reason': 'Niveau de priorité critique détecté par l\'IA',
                'deadline': '2h'
            })
        
        # Gestion des influenceurs à risque
        high_risk_influencers = influencer_analysis.get('risk_assessment', {}).get('high_risk', [])
        if high_risk_influencers:
            recommendations['immediate'].append({
                'action': f'📞 Contact direct avec {len(high_risk_influencers)} influenceur(s) critique(s)',
                'reason': 'Influenceurs à risque élevé identifiés',
                'deadline': '24h'
            })
        
        # Recommandations à court terme
        if web_analysis.get('authenticity_score', 1.0) < 0.6:
            recommendations['short_term'].append({
                'action': '🔍 Investigation approfondie de l\'authenticité',
                'reason': 'Score d\'authenticité faible détecté',
                'timeline': '48h'
            })
        
        # Opportunités de communication
        if any('opportunité' in insight.lower() for insight in sentiment_insights):
            recommendations['short_term'].append({
                'action': '💬 Campagne de communication ciblée',
                'reason': 'Opportunités identifiées par l\'analyse IA',
                'timeline': '1 semaine'
            })
        
        # Recommandations à long terme
        if web_analysis.get('comment_insights', {}).get('total_comments', 0) > 50:
            recommendations['long_term'].append({
                'action': '👥 Programme d\'engagement communautaire',
                'reason': 'Communauté active détectée dans les commentaires',
                'timeline': '1 mois'
            })
        
        # Surveillance continue
        trend_analysis = ai_analysis.get('trends', {})
        if trend_analysis.get('alert_level') in ['modéré', 'élevé']:
            recommendations['long_term'].append({
                'action': '📊 Renforcement du système de surveillance',
                'reason': 'Tendances volatiles détectées',
                'timeline': 'Continu'
            })
        
        return recommendations
    
    def _generate_enhanced_risk_assessment(self, mentions: List, days: int, ai_analysis: Dict) -> Dict:
        """Générer une évaluation de risque enrichie avec l'IA"""
        
        if not mentions:
            return {
                'risk_level': 'FAIBLE',
                'risk_score': 0,
                'ai_assessment': 'Aucune donnée à analyser'
            }
        
        # Calculs de base
        total_mentions = len(mentions)
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        negative_ratio = len(negative_mentions) / total_mentions
        
        avg_engagement = sum(m.engagement_score for m in mentions) / len(mentions)
        max_engagement = max(m.engagement_score for m in mentions)
        
        # Score de base
        volume_score = min(total_mentions / (days * 10), 1.0) * 25
        sentiment_score = negative_ratio * 30
        engagement_score = min((avg_engagement + max_engagement) / 2000, 1.0) * 20
        
        base_risk_score = volume_score + sentiment_score + engagement_score
        
        # Ajustement avec l'IA
        executive_summary = ai_analysis.get('executive_summary', {})
        ai_priority = executive_summary.get('priority_level', 'NORMAL')
        
        ai_adjustment = 0
        if ai_priority == 'CRITIQUE':
            ai_adjustment = 25
        elif ai_priority == 'MODÉRÉ':
            ai_adjustment = 15
        
        # Facteur d'authenticité
        authenticity_score = ai_analysis.get('web_content', {}).get('authenticity_score', 1.0)
        if authenticity_score < 0.5:
            ai_adjustment += 10  # Risque supplémentaire si contenu suspect
        
        final_score = min(base_risk_score + ai_adjustment, 100)
        
        # Déterminer le niveau
        if final_score >= 75:
            risk_level = 'CRITIQUE'
            color = '#dc2626'
        elif final_score >= 50:
            risk_level = 'ÉLEVÉ'
            color = '#ef4444'
        elif final_score >= 30:
            risk_level = 'MODÉRÉ'
            color = '#f59e0b'
        else:
            risk_level = 'FAIBLE'
            color = '#10b981'
        
        return {
            'risk_level': risk_level,
            'risk_score': round(final_score, 1),
            'color': color,
            'ai_assessment': executive_summary.get('summary', 'Analyse IA non disponible'),
            'contributing_factors': {
                'volume': round(volume_score, 1),
                'sentiment': round(sentiment_score, 1),
                'engagement': round(engagement_score, 1),
                'ai_intelligence': ai_adjustment,
                'authenticity_concern': 10 if authenticity_score < 0.5 else 0
            },
            'alert_status': executive_summary.get('key_metrics', {}).get('alert_status', 'NORMAL'),
            'confidence_level': executive_summary.get('key_metrics', {}).get('analysis_confidence', 0.0)
        }
    
    def _extract_web_insights(self, ai_analysis: Dict) -> Dict:
        """Extraire les insights spécifiques au contenu web"""
        
        web_analysis = ai_analysis.get('web_content', {})
        
        if not web_analysis or 'error' in web_analysis:
            return {
                'available': False,
                'reason': 'Analyse web non disponible ou erreur lors de l\'extraction'
            }
        
        article_insights = web_analysis.get('article_insights', [])
        comment_insights = web_analysis.get('comment_insights', {})
        
        return {
            'available': True,
            'articles_analyzed': len(article_insights),
            'total_comments': comment_insights.get('total_comments', 0),
            'unique_commentators': comment_insights.get('unique_authors', 0),
            'top_domains': [article['domain'] for article in article_insights[:5]],
            'most_engaged_comment': comment_insights.get('top_engaged_comments', [{}])[0] if comment_insights.get('top_engaged_comments') else None,
            'authenticity_assessment': web_analysis.get('authenticity_score', 0),
            'key_findings': [
                f"{len(article_insights)} articles analysés en profondeur",
                f"{comment_insights.get('total_comments', 0)} commentaires extraits et analysés",
                f"Score d'authenticité: {web_analysis.get('authenticity_score', 0):.1f}/1.0",
                f"Taux d'engagement: {web_analysis.get('engagement_patterns', {}).get('engagement_rate', 0):.1%}"
            ]
        }

    async def generate_intelligent_html_report(self, report_data: Dict) -> str:
        """Générer le rapport HTML intelligent enrichi"""
        
        # CSS optimisé pour rapport intelligent
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4; margin: 0.8cm; }}
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1f2937; line-height: 1.4; font-size: 9pt; margin: 0; padding: 0; }}
                .header {{ text-align: center; padding: 8px 0; border-bottom: 3px solid #667eea; margin-bottom: 12px; }}
                .header h1 {{ color: #667eea; font-size: 18pt; margin: 0 0 4px 0; font-weight: 700; }}
                .header .subtitle {{ color: #6b7280; font-size: 8pt; line-height: 1.2; }}
                .ai-badge {{ background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 3px 8px; border-radius: 12px; font-size: 7pt; font-weight: bold; margin-left: 8px; }}
                .section-title {{ color: #667eea; font-size: 11pt; font-weight: bold; margin: 10px 0 6px 0; padding-bottom: 3px; border-bottom: 1px solid #e5e7eb; }}
                .ai-section {{ background: linear-gradient(135deg, #667eea15, #764ba205); border-left: 4px solid #667eea; padding: 10px; margin: 8px 0; border-radius: 6px; }}
                .intelligence-metric {{ display: inline-block; background: #f3f4f6; padding: 4px 8px; border-radius: 6px; margin: 2px; font-size: 8pt; }}
                .risk-assessment {{ padding: 12px; border-radius: 8px; margin: 8px 0; }}
                .risk-critique {{ background: #fee2e2; border: 2px solid #dc2626; }}
                .risk-eleve {{ background: #fef2f2; border: 2px solid #ef4444; }}
                .risk-modere {{ background: #fef3c7; border: 2px solid #f59e0b; }}
                .risk-faible {{ background: #f0fdf4; border: 2px solid #10b981; }}
                .web-insight {{ background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 8px; margin: 6px 0; }}
                .recommendation {{ background: #fafafa; border-left: 3px solid #8b5cf6; padding: 8px; margin: 4px 0; }}
                .recommendation.immediate {{ border-left-color: #ef4444; background: #fef2f2; }}
                .recommendation.short-term {{ border-left-color: #f59e0b; background: #fffbeb; }}
                .recommendation.long-term {{ border-left-color: #10b981; background: #f0fdf4; }}
                .authenticity-indicator {{ display: flex; align-items: center; margin: 4px 0; }}
                .authenticity-bar {{ width: 100px; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; margin: 0 8px; }}
                .authenticity-fill {{ height: 100%; background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981); }}
                table {{ width: 100%; border-collapse: collapse; font-size: 8pt; margin: 6px 0; }}
                th {{ background: #667eea; color: white; padding: 4px; text-align: left; }}
                td {{ padding: 4px; border-bottom: 1px solid #e5e7eb; }}
                .insight-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 6px; border-radius: 4px; margin: 4px 0; font-size: 8pt; }}
            </style>
        </head>
        <body>
        
        <!-- En-tête -->
        <div class="header">
            <h1>🤖 RAPPORT INTELLIGENT - ANALYSE IA AVANCÉE</h1>
            <div class="subtitle">
                <strong>{report_data['report_object']}</strong>
                <span class="ai-badge">IA SOUVERAINE</span><br>
                Période: {report_data['period_days']} jours | Généré: {report_data['generated_at'].strftime('%d/%m/%Y %H:%M')}<br>
                Mots-clés: {', '.join(report_data['keywords'])} | Total mentions: {report_data['total_mentions']}
                {f" | Contenu web analysé: {report_data['web_content_analyzed']} sources" if report_data.get('web_content_analyzed', 0) > 0 else ""}
            </div>
        </div>
        """
        
        # Synthèse exécutive IA
        if 'ai_analysis' in report_data and 'executive_summary' in report_data['ai_analysis']:
            executive = report_data['ai_analysis']['executive_summary']
            priority_class = f"risk-{executive.get('priority_level', 'normal').lower()}"
            confidence = executive.get('key_metrics', {}).get('analysis_confidence', 0.0)
            
            html += f"""
            <div class="section-title">🧠 SYNTHÈSE EXÉCUTIVE IA</div>
            <div class="ai-section {priority_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 11pt;">NIVEAU DE PRIORITÉ: {executive.get('priority_level', 'NORMAL')}</strong>
                    <div>
                        <span style="font-size: 7pt;">Confiance IA: {confidence*100:.0f}%</span>
                        <div style="display: inline-block; width: 40px; height: 6px; background: #e5e7eb; border-radius: 3px; margin-left: 5px; overflow: hidden;">
                            <div style="width: {confidence*100}%; height: 100%; background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);"></div>
                        </div>
                    </div>
                </div>
                <p style="margin: 6px 0;"><strong>🎯 Analyse:</strong> {executive.get('summary', 'Analyse IA en cours...')}</p>
                <p style="font-size: 8pt; margin: 4px 0; color: #4b5563;"><strong>📊 Statut:</strong> {executive.get('key_metrics', {}).get('alert_status', 'Normal')}</p>
                {f"<p style='font-size: 8pt; margin: 4px 0; color: #4b5563;'><strong>🌐 Sources web analysées:</strong> {executive.get('key_metrics', {}).get('web_content_analyzed', 0)}</p>" if executive.get('key_metrics', {}).get('web_content_analyzed', 0) > 0 else ""}
            </div>
            """
        
        # Analyse intelligente
        if 'smart_analysis' in report_data:
            smart = report_data['smart_analysis']
            html += f"""
            <div class="section-title">🎯 ANALYSE INTELLIGENTE</div>
            <div class="ai-section">
                <p><strong>Résumé:</strong> {smart['summary']}</p>
                <div style="margin: 8px 0;">
                    <strong>Métriques d'intelligence:</strong>
                    <div style="margin-top: 4px;">
                        <span class="intelligence-metric">🚀 Viralité: {smart['intelligence_metrics']['virality_score']:.2f}</span>
                        <span class="intelligence-metric">🌐 Diversité: {smart['intelligence_metrics']['diversity_score']:.2f}</span>
                        <span class="intelligence-metric">📊 Engagement moy: {smart['intelligence_metrics']['avg_engagement']:.1f}</span>
                        <span class="intelligence-metric">🤖 Confiance IA: {smart['intelligence_metrics']['ai_confidence']:.1%}</span>
                    </div>
                </div>
                <div><strong>💡 Insights clés:</strong></div>
                <ul style="margin: 4px 0; padding-left: 15px; font-size: 8pt;">
                    {chr(10).join([f'<li>{insight}</li>' for insight in smart['key_insights'] if insight.strip()])}
                </ul>
                {f"<div class='web-insight'><strong>🌐 Contexte web:</strong> {smart.get('web_context', '')}</div>" if smart.get('web_context') else ""}
            </div>
            """
        
        # Évaluation de risque enrichie IA
        if 'risk_assessment' in report_data:
            risk = report_data['risk_assessment']
            risk_class = f"risk-{risk['risk_level'].lower().replace('é', 'e')}"
            
            html += f"""
            <div class="section-title">🚨 ÉVALUATION DE RISQUE IA</div>
            <div class="risk-assessment {risk_class}">
                <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 12pt;">NIVEAU: {risk['risk_level']} ({risk['risk_score']}/100)</strong>
                    <span style="font-size: 8pt; margin-left: auto;">Confiance: {risk['confidence_level']:.1%}</span>
                </div>
                <p style="margin: 6px 0;"><strong>🤖 Évaluation IA:</strong> {risk['ai_assessment']}</p>
                <p style="font-size: 8pt; margin: 4px 0;"><strong>📈 Statut d'alerte:</strong> {risk['alert_status']}</p>
                
                <div style="margin-top: 8px;">
                    <strong style="font-size: 9pt;">Facteurs contributifs:</strong>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; margin-top: 4px; font-size: 7pt;">
                        <div>Volume: {risk['contributing_factors']['volume']}</div>
                        <div>Sentiment: {risk['contributing_factors']['sentiment']}</div>
                        <div>Engagement: {risk['contributing_factors']['engagement']}</div>
                        <div>IA Intelligence: {risk['contributing_factors']['ai_intelligence']}</div>
                        <div>Authenticité: {risk['contributing_factors']['authenticity_concern']}</div>
                    </div>
                </div>
            </div>
            """
        
        # Évaluation d'authenticité
        if 'authenticity_assessment' in report_data:
            auth = report_data['authenticity_assessment']
            html += f"""
            <div class="section-title">🔍 ÉVALUATION D'AUTHENTICITÉ</div>
            <div class="ai-section">
                <div class="authenticity-indicator">
                    <strong>{auth['authenticity_level']}</strong>
                    <div class="authenticity-bar">
                        <div class="authenticity-fill" style="width: {auth['authenticity_score']*100}%;"></div>
                    </div>
                    <span>{auth['authenticity_score']}/1.0</span>
                    <span style="margin-left: 8px; font-size: 7pt; color: {auth['color']};">●</span>
                </div>
                
                <div style="margin: 6px 0;">
                    <strong>Indicateurs positifs:</strong>
                    <ul style="margin: 2px 0; padding-left: 15px; font-size: 8pt;">
                        {chr(10).join([f'<li>{indicator}</li>' for indicator in auth['indicators']])}
                    </ul>
                </div>
                
                {f"<div style='margin: 6px 0;'><strong>🚩 Signaux d'alarme:</strong><ul style='margin: 2px 0; padding-left: 15px; font-size: 8pt;'>{chr(10).join([f'<li style=\"color: #ef4444;\">{flag}</li>' for flag in auth['red_flags']])}</ul></div>" if auth.get('red_flags') else ""}
                
                <p style="font-size: 7pt; margin: 4px 0; color: #6b7280;">Confiance de l'évaluation: {auth['confidence']}</p>
            </div>
            """
        
        # Insights web spécifiques
        if 'web_insights' in report_data and report_data['web_insights'].get('available'):
            web = report_data['web_insights']
            html += f"""
            <div class="section-title">🌐 ANALYSE CONTENU WEB</div>
            <div class="web-insight">
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 8px; font-size: 8pt;">
                    <div><strong>{web['articles_analyzed']}</strong><br>Articles analysés</div>
                    <div><strong>{web['total_comments']}</strong><br>Commentaires extraits</div>
                    <div><strong>{web['unique_commentators']}</strong><br>Commentateurs uniques</div>
                    <div><strong>{web['authenticity_assessment']:.1f}/1.0</strong><br>Score authenticité</div>
                </div>
                
                <div><strong>🔍 Résultats clés:</strong></div>
                <ul style="margin: 4px 0; padding-left: 15px; font-size: 8pt;">
                    {chr(10).join([f'<li>{finding}</li>' for finding in web['key_findings']])}
                </ul>
                
                {f"<div style='margin-top: 6px;'><strong>💬 Commentaire le plus engageant:</strong><br><em style='font-size: 7pt;'>\"{web['most_engaged_comment']['text'][:100]}...\" - {web['most_engaged_comment']['author']} ({web['most_engaged_comment']['likes']} likes)</em></div>" if web.get('most_engaged_comment') else ""}
            </div>
            """
        
        # Patterns d'engagement intelligents
        if 'engagement_insights' in report_data:
            engagement = report_data['engagement_insights']
            html += f"""
            <div class="section-title">📊 PATTERNS D'ENGAGEMENT IA</div>
            <div class="ai-section">
                <p><strong>Pattern détecté:</strong> {engagement['pattern']}</p>
                
                <div style="margin: 6px 0;">
                    <strong>Indicateurs d'authenticité:</strong>
                    <span class="intelligence-metric">🌐 Authenticité web: {engagement['authenticity_indicators']['web_authenticity']:.1f}</span>
                    <span class="intelligence-metric">💬 Qualité commentaires: {engagement['authenticity_indicators']['comment_quality']}</span>
                </div>
                
                <div><strong>💡 Insights:</strong></div>
                <ul style="margin: 4px 0; padding-left: 15px; font-size: 8pt;">
                    {chr(10).join([f'<li>{insight}</li>' for insight in engagement['insights']])}
                </ul>
            </div>
            """
        
        # Recommandations actionnables
        if 'actionable_recommendations' in report_data:
            recs = report_data['actionable_recommendations']
            html += f"""
            <div class="section-title">🎯 RECOMMANDATIONS ACTIONNABLES IA</div>
            """
            
            for priority, actions in recs.items():
                if actions:
                    priority_labels = {
                        'immediate': '🚨 ACTIONS IMMÉDIATES',
                        'short_term': '⚡ COURT TERME',
                        'long_term': '🎯 LONG TERME'
                    }
                    
                    html += f"<div style='margin: 8px 0;'><strong>{priority_labels.get(priority, priority.upper())}</strong></div>"
                    
                    for action in actions:
                        deadline_key = 'deadline' if 'deadline' in action else 'timeline'
                        html += f"""
                        <div class="recommendation {priority}">
                            <strong>{action['action']}</strong><br>
                            <span style="font-size: 8pt;">{action['reason']}</span><br>
                            <span style="font-size: 7pt; color: #6b7280;">⏰ {action.get(deadline_key, 'Non spécifié')}</span>
                        </div>
                        """
        
        # Footer avec info IA
        html += """
            <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #e5e7eb; text-align: center; font-size: 7pt; color: #9ca3af;">
                <p>🤖 Rapport généré avec Intelligence Artificielle Souveraine • Agents IA Spécialisés • Analyse Web Avancée</p>
                <p style="margin-top: 4px;">🧠 Sentiment • 📈 Tendances • 👑 Influenceurs • 🌐 Contenu Web • 🔍 Authenticité</p>
            </div>
        </body>
        </html>
        """
        
        return html

    async def generate_intelligent_pdf(self, report_data: Dict) -> bytes:
        """Générer le PDF du rapport intelligent"""
        try:
            from weasyprint import HTML
            
            html_content = await self.generate_intelligent_html_report(report_data)
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            return pdf_bytes
            
        except ImportError:
            logger.warning("WeasyPrint not available, generating HTML only")
            html_content = await self.generate_intelligent_html_report(report_data)
            return html_content.encode('utf-8')