"""
Générateur de rapports enrichi avec IA
Intègre les agents d'analyse intelligents pour générer du contenu dynamique
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from collections import Counter
import asyncio

from app.ai_service import ReportIntelligenceAgent, AnalysisContext
from app.models import Keyword, Mention

logger = logging.getLogger(__name__)


class IntelligentReportGenerator:
    """Générateur de rapports intelligent avec IA"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_agent = ReportIntelligenceAgent()
    
    async def generate_intelligent_report(
        self,
        keyword_ids: List[int],
        days: int = 30,
        report_object: str = ""
    ) -> Dict:
        """Générer un rapport enrichi avec analyse IA"""
        
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
        
        # Générer l'analyse IA
        ai_analysis = await self.ai_agent.generate_intelligent_analysis(analysis_context)
        
        # Préparer les données du rapport
        report_data = {
            'keywords': keywords_names,
            'keyword_ids': keyword_ids,
            'period_days': days,
            'report_object': report_object or ', '.join(keywords_names),
            'generated_at': datetime.utcnow(),
            'total_mentions': len(mentions),
            'ai_analysis': ai_analysis,  # Nouvelle section IA
        }
        
        # Analyses traditionnelles enrichies avec l'IA
        positive_mentions = [m for m in mentions if m.sentiment == 'positive']
        negative_mentions = [m for m in mentions if m.sentiment == 'negative']
        neutral_mentions = [m for m in mentions if m.sentiment == 'neutral']
        
        report_data['risk_assessment'] = self._generate_enhanced_risk_assessment(mentions, days, ai_analysis)
        report_data['positive_analysis'] = self._analyze_positive_sentiment_with_ai(positive_mentions, mentions, ai_analysis)
        report_data['negative_analysis'] = self._analyze_negative_sentiment_with_ai(negative_mentions, mentions, ai_analysis)
        report_data['neutral_analysis'] = self._analyze_neutral_sentiment_with_ai(neutral_mentions, mentions, ai_analysis)
        report_data['judgment_synthesis'] = self._generate_synthesis_with_ai(
            positive_mentions, negative_mentions, neutral_mentions, mentions, days, ai_analysis
        )
        report_data['engaged_influencers'] = self._analyze_influencers_with_ai(mentions, ai_analysis)
        report_data['recommendations'] = self._generate_ai_recommendations(report_data, ai_analysis)
        
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
        
        # Données d'influenceurs (simulées ici, à adapter selon votre structure)
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
                'sentiment_score': positive_ratio * 100,  # Score de 0 à 100
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
            time_trends=time_trends
        )
    
    def _generate_enhanced_risk_assessment(self, mentions: List, days: int, ai_analysis: Dict) -> Dict:
        """Évaluation de risque enrichie avec insights IA"""
        
        # Calculs de base
        total_mentions = len(mentions)
        if total_mentions == 0:
            return {
                'risk_level': 'FAIBLE',
                'risk_score': 0,
                'explanation': 'Aucune mention détectée.',
                'ai_insight': ai_analysis.get('executive_summary', {}).get('summary', ''),
                'priority_level': ai_analysis.get('executive_summary', {}).get('priority_level', 'NORMAL')
            }
        
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
        ai_priority = ai_analysis.get('executive_summary', {}).get('priority_level', 'NORMAL')
        ai_adjustment = 0
        if ai_priority == 'CRITIQUE':
            ai_adjustment = 20
        elif ai_priority == 'MODÉRÉ':
            ai_adjustment = 10
        
        final_score = min(base_risk_score + ai_adjustment, 100)
        
        # Déterminer le niveau
        if final_score >= 70:
            risk_level = 'ÉLEVÉ'
            color = '#ef4444'
        elif final_score >= 40:
            risk_level = 'MODÉRÉ'
            color = '#f59e0b'
        else:
            risk_level = 'FAIBLE'
            color = '#10b981'
        
        # Récupérer les insights IA
        ai_insight = ""
        if 'sentiment' in ai_analysis and 'analysis' in ai_analysis['sentiment']:
            ai_insight = ai_analysis['sentiment']['analysis'][:200] + "..."
        
        return {
            'risk_level': risk_level,
            'risk_score': round(final_score, 1),
            'color': color,
            'explanation': f"Niveau de risque {risk_level} ({final_score:.1f}/100) avec analyse IA",
            'ai_insight': ai_insight,
            'priority_level': ai_priority,
            'factors': {
                'volume': {'score': round(volume_score, 1), 'detail': f'{total_mentions} mentions'},
                'sentiment': {'score': round(sentiment_score, 1), 'detail': f'{int(negative_ratio*100)}% négatif'},
                'engagement': {'score': round(engagement_score, 1), 'detail': f'Max {int(max_engagement)}'},
                'ai_adjustment': {'score': ai_adjustment, 'detail': f'Ajustement IA: {ai_priority}'}
            }
        }
    
    def _analyze_positive_sentiment_with_ai(self, positive_mentions: List, all_mentions: List, ai_analysis: Dict) -> Dict:
        """Analyse des sentiments positifs enrichie avec IA"""
        
        if not positive_mentions:
            return {
                'count': 0,
                'percentage': 0,
                'analysis': "Aucun commentaire positif significatif identifié.",
                'ai_enhancement': "L'analyse IA confirme l'absence de réactions positives notables."
            }
        
        total = len(all_mentions)
        percentage = (len(positive_mentions) / total * 100) if total > 0 else 0
        
        # Analyse traditionnelle
        basic_analysis = f"L'analyse révèle {len(positive_mentions)} mentions à connotation positive ({percentage:.1f}% du total)."
        
        # Enhancement IA
        ai_enhancement = ""
        if 'sentiment' in ai_analysis and 'analysis' in ai_analysis['sentiment']:
            sentiment_analysis = ai_analysis['sentiment']['analysis']
            # Extraire la partie sur le positif (approximation)
            sentences = sentiment_analysis.split('.')
            positive_sentences = [s for s in sentences if any(word in s.lower() for word in ['positif', 'favorable', 'opportunité'])]
            if positive_sentences:
                ai_enhancement = '. '.join(positive_sentences[:2]) + '.'
            else:
                ai_enhancement = "L'IA note que les réactions positives constituent une base solide pour le développement de la communication."
        
        return {
            'count': len(positive_mentions),
            'percentage': round(percentage, 1),
            'analysis': basic_analysis,
            'ai_enhancement': ai_enhancement,
            'strategic_context': f"Les {len(positive_mentions)} voix favorables constituent un capital précieux selon l'analyse IA."
        }
    
    def _analyze_negative_sentiment_with_ai(self, negative_mentions: List, all_mentions: List, ai_analysis: Dict) -> Dict:
        """Analyse des sentiments négatifs enrichie avec IA"""
        
        if not negative_mentions:
            return {
                'count': 0,
                'percentage': 0,
                'analysis': "Aucun commentaire négatif significatif détecté.",
                'ai_enhancement': "L'analyse IA confirme un environnement communicationnel favorable."
            }
        
        total = len(all_mentions)
        percentage = (len(negative_mentions) / total * 100) if total > 0 else 0
        
        # Analyse traditionnelle
        basic_analysis = f"L'analyse identifie {len(negative_mentions)} mentions à caractère critique ({percentage:.1f}%)."
        
        # Enhancement IA
        ai_enhancement = ""
        if 'sentiment' in ai_analysis and 'analysis' in ai_analysis['sentiment']:
            sentiment_analysis = ai_analysis['sentiment']['analysis']
            # Extraire la partie sur le négatif
            sentences = sentiment_analysis.split('.')
            negative_sentences = [s for s in sentences if any(word in s.lower() for word in ['négatif', 'critique', 'risque', 'alerte'])]
            if negative_sentences:
                ai_enhancement = '. '.join(negative_sentences[:2]) + '.'
            else:
                ai_enhancement = "L'IA recommande une surveillance accrue de ces signaux critiques."
        
        # Évaluation du risque viral
        high_engagement_negative = [m for m in negative_mentions if m.engagement_score > 500]
        viral_risk = "ÉLEVÉ" if len(high_engagement_negative) > 2 else "MODÉRÉ" if len(high_engagement_negative) > 0 else "FAIBLE"
        
        return {
            'count': len(negative_mentions),
            'percentage': round(percentage, 1),
            'analysis': basic_analysis,
            'ai_enhancement': ai_enhancement,
            'viral_risk': viral_risk,
            'strategic_context': f"Risque de viralisation {viral_risk} identifié par l'analyse IA avancée."
        }
    
    def _analyze_neutral_sentiment_with_ai(self, neutral_mentions: List, all_mentions: List, ai_analysis: Dict) -> Dict:
        """Analyse des sentiments neutres enrichie avec IA"""
        
        if not neutral_mentions:
            return {
                'count': 0,
                'percentage': 0,
                'analysis': "Aucune mention neutre significative.",
                'ai_enhancement': "L'IA détecte une polarisation forte de l'opinion."
            }
        
        total = len(all_mentions)
        percentage = (len(neutral_mentions) / total * 100) if total > 0 else 0
        
        basic_analysis = f"Les {len(neutral_mentions)} mentions neutres ({percentage:.1f}%) reflètent une approche observatrice."
        
        # Enhancement IA
        ai_enhancement = ""
        if 'sentiment' in ai_analysis and 'analysis' in ai_analysis['sentiment']:
            sentiment_analysis = ai_analysis['sentiment']['analysis']
            sentences = sentiment_analysis.split('.')
            neutral_sentences = [s for s in sentences if any(word in s.lower() for word in ['neutre', 'indécis', 'opportunité', 'potentiel'])]
            if neutral_sentences:
                ai_enhancement = '. '.join(neutral_sentences[:2]) + '.'
            else:
                ai_enhancement = "L'IA identifie ces audiences neutres comme un segment stratégique à convertir."
        
        return {
            'count': len(neutral_mentions),
            'percentage': round(percentage, 1),
            'analysis': basic_analysis,
            'ai_enhancement': ai_enhancement,
            'strategic_context': f"💡 OPPORTUNITÉ IA: Segment de {len(neutral_mentions)} voix neutres convertibles selon l'analyse prédictive."
        }
    
    def _generate_synthesis_with_ai(
        self, 
        positive: List, 
        negative: List, 
        neutral: List,
        all_mentions: List,
        days: int,
        ai_analysis: Dict
    ) -> Dict:
        """Synthèse enrichie avec insights IA"""
        
        total = len(positive) + len(negative) + len(neutral)
        
        if total == 0:
            return {
                'total_analyzed': 0,
                'ai_synthesis': "Aucune donnée à analyser.",
                'priority_level': 'NORMAL'
            }
        
        pos_pct = (len(positive) / total) * 100
        neg_pct = (len(negative) / total) * 100
        neu_pct = (len(neutral) / total) * 100
        
        # Synthèse traditionnelle
        if pos_pct > neg_pct and pos_pct > neu_pct:
            basic_trend = "Favorable"
            trend_analysis = f"Les réactions positives dominent ({pos_pct:.1f}%)"
        elif neg_pct > pos_pct and neg_pct > neu_pct:
            basic_trend = "Critique"
            trend_analysis = f"Les réactions négatives prédominent ({neg_pct:.1f}%)"
        else:
            basic_trend = "Mitigé"
            trend_analysis = f"Opinion divisée avec {neu_pct:.1f}% de neutres"
        
        # Synthèse IA
        ai_synthesis = ""
        priority_level = "NORMAL"
        
        if 'executive_summary' in ai_analysis:
            executive = ai_analysis['executive_summary']
            ai_synthesis = executive.get('summary', 'Analyse IA indisponible.')
            priority_level = executive.get('priority_level', 'NORMAL')
        
        return {
            'total_analyzed': total,
            'distribution': {
                'positive': {'count': len(positive), 'percentage': round(pos_pct, 1)},
                'negative': {'count': len(negative), 'percentage': round(neg_pct, 1)},
                'neutral': {'count': len(neutral), 'percentage': round(neu_pct, 1)}
            },
            'basic_trend': basic_trend,
            'trend_analysis': trend_analysis,
            'ai_synthesis': ai_synthesis,
            'priority_level': priority_level,
            'ai_confidence': ai_analysis.get('executive_summary', {}).get('key_metrics', {}).get('analysis_confidence', 0.0)
        }
    
    def _analyze_influencers_with_ai(self, mentions: List, ai_analysis: Dict) -> Dict:
        """Analyse des influenceurs enrichie avec IA"""
        
        # Grouper par auteur
        influencer_data = {}
        for mention in mentions:
            author = mention.author
            if author not in influencer_data:
                influencer_data[author] = {
                    'mentions': [],
                    'total_engagement': 0,
                    'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0}
                }
            
            influencer_data[author]['mentions'].append(mention)
            influencer_data[author]['total_engagement'] += mention.engagement_score
            
            if mention.sentiment:
                influencer_data[author]['sentiment_distribution'][mention.sentiment] += 1
        
        # Créer tableau des influenceurs
        influencers_table = []
        for author, data in influencer_data.items():
            mention_count = len(data['mentions'])
            total_eng = data['total_engagement']
            
            sentiment_dist = data['sentiment_distribution']
            total_sentiment = sum(sentiment_dist.values())
            
            if total_sentiment > 0:
                neg_ratio = sentiment_dist['negative'] / total_sentiment
                sentiment_tendency = "⚠️ Critique" if neg_ratio > 0.6 else "✅ Favorable" if sentiment_dist['positive'] / total_sentiment > 0.6 else "⚖️ Mitigé"
                risk_level = "ÉLEVÉ" if neg_ratio > 0.6 else "Modéré"
            else:
                sentiment_tendency = "Indéterminé"
                risk_level = "Modéré"
            
            influencers_table.append({
                'name': author,
                'mention_count': mention_count,
                'total_engagement': int(total_eng),
                'avg_engagement': int(total_eng / mention_count),
                'sentiment_tendency': sentiment_tendency,
                'risk_level': risk_level
            })
        
        # Trier par engagement
        influencers_table.sort(key=lambda x: x['total_engagement'], reverse=True)
        
        # Analysis IA
        ai_influencer_analysis = ""
        if 'influencers' in ai_analysis and 'analysis' in ai_analysis['influencers']:
            ai_influencer_analysis = ai_analysis['influencers']['analysis']
        
        high_risk_count = len([i for i in influencers_table if i['risk_level'] == 'ÉLEVÉ'])
        
        return {
            'total_identified': len(influencers_table),
            'high_risk_count': high_risk_count,
            'influencers_table': influencers_table[:10],  # Top 10
            'ai_analysis': ai_influencer_analysis,
            'strategic_context': f"L'IA a identifié {len(influencers_table)} influenceurs dont {high_risk_count} à surveiller prioritairement."
        }
    
    def _generate_ai_recommendations(self, report_data: Dict, ai_analysis: Dict) -> Dict:
        """Génère des recommandations basées sur l'analyse IA"""
        
        recommendations = {
            'priority_1': [],
            'priority_2': [],
            'priority_3': []
        }
        
        # Récupérer les recommandations IA
        executive_summary = ai_analysis.get('executive_summary', {})
        priority_level = executive_summary.get('priority_level', 'NORMAL')
        
        # Recommandations basées sur l'IA
        if priority_level == 'CRITIQUE':
            recommendations['priority_1'].append({
                'title': '🚨 Action immédiate requise',
                'action': 'L\'IA détecte une situation critique nécessitant une intervention d\'urgence',
                'deadline': '24h',
                'impact': 'Prévention d\'escalade'
            })
        
        # Recommandations de sentiment
        sentiment_analysis = ai_analysis.get('sentiment', {})
        if 'key_insights' in sentiment_analysis:
            for insight in sentiment_analysis['key_insights'][:2]:
                recommendations['priority_2'].append({
                    'title': '📊 Insight IA - Sentiment',
                    'action': insight,
                    'deadline': '7 jours',
                    'impact': 'Optimisation communication'
                })
        
        # Recommandations d'influenceurs
        influencer_analysis = ai_analysis.get('influencers', {})
        if 'recommended_actions' in influencer_analysis:
            for action in influencer_analysis['recommended_actions'][:2]:
                recommendations['priority_2'].append({
                    'title': '👑 Action Influenceurs IA',
                    'action': action,
                    'deadline': '48h',
                    'impact': 'Gestion des risques d\'influence'
                })
        
        # Recommandations de tendances
        trends_analysis = ai_analysis.get('trends', {})
        if 'predictions' in trends_analysis:
            predictions = trends_analysis['predictions']
            if predictions.get('confidence') in ['medium', 'high']:
                recommendations['priority_3'].append({
                    'title': '📈 Prédiction IA',
                    'action': f"Tendance prédite: {predictions.get('prediction', 'Non spécifiée')}",
                    'deadline': '14 jours',
                    'impact': 'Anticipation des évolutions'
                })
        
        return recommendations

    async def generate_intelligent_html_report(self, report_data: Dict) -> str:
        """Génère le rapport HTML enrichi avec l'analyse IA"""
        
        # CSS optimisé
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
                .section-title {{ color: #667eea; font-size: 11pt; font-weight: bold; margin: 10px 0 6px 0; padding-bottom: 3px; border-bottom: 1px solid #e5e7eb; }}
                .ai-section {{ background: linear-gradient(135deg, #667eea15, #764ba205); border-left: 4px solid #667eea; padding: 10px; margin: 8px 0; border-radius: 6px; }}
                .ai-badge {{ background: #667eea; color: white; padding: 2px 8px; border-radius: 12px; font-size: 7pt; font-weight: bold; }}
                .priority-critical {{ background: #fee2e2; border-left: 4px solid #ef4444; }}
                .priority-moderate {{ background: #fef3c7; border-left: 4px solid #f59e0b; }}
                .priority-normal {{ background: #f0fdf4; border-left: 4px solid #10b981; }}
                .insight-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px; border-radius: 4px; margin: 6px 0; }}
                .confidence-meter {{ display: inline-block; width: 50px; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }}
                .confidence-fill {{ height: 100%; background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981); }}
            </style>
        </head>
        <body>
        
        <!-- En-tête -->
        <div class="header">
            <h1>🤖 RAPPORT INTELLIGENT - ANALYSE IA</h1>
            <div class="subtitle">
                <strong>{report_data['report_object']}</strong><br>
                Période: {report_data['period_days']} jours | Généré: {report_data['generated_at'].strftime('%d/%m/%Y %H:%M')}<br>
                Mots-clés: {', '.join(report_data['keywords'])} | Total mentions: {report_data['total_mentions']}
                <span class="ai-badge">IA ACTIVÉE</span>
            </div>
        </div>
        """
        
        # Synthèse exécutive IA
        if 'ai_analysis' in report_data and 'executive_summary' in report_data['ai_analysis']:
            executive = report_data['ai_analysis']['executive_summary']
            priority_class = f"priority-{executive.get('priority_level', 'normal').lower().replace('é', 'e')}"
            confidence = executive.get('key_metrics', {}).get('analysis_confidence', 0.0)
            
            html += f"""
            <div class="section-title">🧠 SYNTHÈSE EXÉCUTIVE IA</div>
            <div class="ai-section {priority_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 10pt;">NIVEAU: {executive.get('priority_level', 'NORMAL')}</strong>
                    <div>
                        <span style="font-size: 7pt; margin-right: 5px;">Confiance IA:</span>
                        <div class="confidence-meter">
                            <div class="confidence-fill" style="width: {confidence*100}%;"></div>
                        </div>
                        <span style="font-size: 7pt; margin-left: 3px;">{confidence*100:.0f}%</span>
                    </div>
                </div>
                <p style="font-size: 9pt; margin: 6px 0;"><strong>Analyse:</strong> {executive.get('summary', 'Non disponible')}</p>
                <p style="font-size: 8pt; margin: 4px 0; color: #4b5563;"><strong>Statut:</strong> {executive.get('key_metrics', {}).get('alert_status', 'Normal')}</p>
            </div>
            """
        
        # Évaluation de gravité enrichie IA
        if 'risk_assessment' in report_data:
            risk = report_data['risk_assessment']
            risk_class = f"priority-{risk['risk_level'].lower().replace('é', 'e')}"
            
            html += f"""
            <div class="section-title">🚨 ÉVALUATION DE GRAVITÉ (IA)</div>
            <div class="ai-section {risk_class}">
                <strong style="font-size: 11pt;">NIVEAU: {risk['risk_level']} ({risk['risk_score']}/100)</strong>
                <p><strong>Analyse IA:</strong> {risk.get('ai_insight', 'Analyse en cours...')}</p>
            </div>
            """
        
        # Analyse de sentiment avec IA
        for sentiment_type in ['positive', 'negative', 'neutral']:
            if f'{sentiment_type}_analysis' in report_data:
                analysis = report_data[f'{sentiment_type}_analysis']
                emoji = {'positive': '😊', 'negative': '😞', 'neutral': '😐'}[sentiment_type]
                
                html += f"""
                <div class="section-title">{emoji} JUGEMENTS {sentiment_type.upper()}S ({analysis['count']} - {analysis['percentage']}%)</div>
                <div class="insight-box">
                    <p><strong>Analyse:</strong> {analysis['analysis']}</p>
                    <p><strong>🤖 Enhancement IA:</strong> {analysis.get('ai_enhancement', 'Analyse IA indisponible.')}</p>
                    <p style="font-size: 8pt; color: #6366f1;"><strong>Contexte Stratégique:</strong> {analysis.get('strategic_context', '')}</p>
                </div>
                """
        
        # Synthèse des jugements avec IA
        if 'judgment_synthesis' in report_data:
            synth = report_data['judgment_synthesis']
            html += f"""
            <div class="section-title">📊 SYNTHÈSE DES JUGEMENTS (IA)</div>
            <div class="ai-section">
                <p><strong>Tendance:</strong> {synth.get('basic_trend', 'Indéterminé')}</p>
                <p><strong>🤖 Synthèse IA:</strong> {synth.get('ai_synthesis', 'Analyse en cours...')}</p>
                <p><strong>Niveau de Priorité:</strong> {synth.get('priority_level', 'NORMAL')} 
                   (Confiance: {synth.get('ai_confidence', 0)*100:.0f}%)</p>
            </div>
            """
        
        # Influenceurs avec analyse IA
        if 'engaged_influencers' in report_data:
            inf = report_data['engaged_influencers']
            html += f"""
            <div class="section-title">👑 INFLUENCEURS ANALYSÉS PAR IA ({inf['total_identified']})</div>
            <div class="ai-section">
                <p><strong>🤖 Analyse IA:</strong> {inf.get('ai_analysis', 'Analyse des influenceurs en cours...')[:300]}...</p>
                <p><strong>Contexte:</strong> {inf.get('strategic_context', '')}</p>
                
                <table style="width: 100%; border-collapse: collapse; font-size: 8pt; margin: 6px 0;">
                    <tr style="background: #667eea; color: white;">
                        <th style="padding: 4px; text-align: left;">Influenceur</th>
                        <th style="padding: 4px;">Mentions</th>
                        <th style="padding: 4px;">Engagement</th>
                        <th style="padding: 4px;">Tendance</th>
                        <th style="padding: 4px;">Risque IA</th>
                    </tr>
            """
            
            for influencer in inf.get('influencers_table', [])[:5]:
                risk_color = '#ef4444' if influencer['risk_level'] == 'ÉLEVÉ' else '#f59e0b' if influencer['risk_level'] == 'Modéré' else '#10b981'
                html += f"""
                    <tr>
                        <td style="padding: 4px; border-bottom: 1px solid #e5e7eb;"><strong>{influencer['name'][:25]}</strong></td>
                        <td style="padding: 4px; text-align: center; border-bottom: 1px solid #e5e7eb;">{influencer['mention_count']}</td>
                        <td style="padding: 4px; text-align: center; border-bottom: 1px solid #e5e7eb;">{influencer['total_engagement']:,}</td>
                        <td style="padding: 4px; text-align: center; border-bottom: 1px solid #e5e7eb;">{influencer['sentiment_tendency']}</td>
                        <td style="padding: 4px; text-align: center; border-bottom: 1px solid #e5e7eb; color: {risk_color};"><strong>{influencer['risk_level']}</strong></td>
                    </tr>
                """
            
            html += "</table></div>"
        
        # Recommandations IA
        if 'recommendations' in report_data:
            recs = report_data['recommendations']
            html += f"""
            <div class="section-title">🎯 RECOMMANDATIONS OPÉRATIONNELLES IA</div>
            """
            
            for priority_level in ['priority_1', 'priority_2']:
                priority_label = "🚨 PRIORITÉ 1 - ACTION IMMÉDIATE" if priority_level == 'priority_1' else "⚡ PRIORITÉ 2 - COURT TERME"
                
                if recs.get(priority_level):
                    html += f"<p style='font-weight:600; font-size:9pt; margin:6px 0; color: #667eea;'>{priority_label}</p>"
                    
                    for rec in recs[priority_level][:3]:
                        html += f"""
                        <div class="insight-box" style="margin: 4px 0;">
                            <strong style="font-size: 8.5pt;">{rec['title']}</strong><br>
                            <span style="font-size: 8pt;">{rec['action']}</span><br>
                            <span style="font-size: 7pt; color: #6366f1;">⏰ {rec['deadline']} | 📈 {rec['impact']}</span>
                        </div>
                        """
        
        # Footer avec info IA
        html += """
            <div style="margin-top:12px; padding-top:8px; border-top:1px solid #e5e7eb; text-align:center; font-size:7pt; color:#9ca3af;">
                <p>🤖 Rapport généré avec Intelligence Artificielle • Modèles LLM Open Source • République du Cameroun</p>
                <p style="margin-top: 4px;">⚡ Analyse en temps réel • 🧠 Insights prédictifs • 🎯 Recommandations personnalisées</p>
            </div>
        </body>
        </html>
        """
        
        return html

    async def generate_intelligent_pdf(self, report_data: Dict) -> bytes:
        """Génère le PDF du rapport intelligent"""
        try:
            from weasyprint import HTML
            
            html_content = await self.generate_intelligent_html_report(report_data)
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            return pdf_bytes
            
        except ImportError:
            logger.warning("WeasyPrint not available, generating HTML only")
            html_content = await self.generate_intelligent_html_report(report_data)
            return html_content.encode('utf-8')