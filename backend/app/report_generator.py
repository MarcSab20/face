"""
Service de génération de rapports PDF professionnels - Version 2
Avec analyse détaillée et réponses aux questions stratégiques
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Générateur de rapports PDF avec analyse intelligente"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_keyword_report(
        self,
        keyword_ids: List[int],
        days: int = 30,
        report_object: str = "",
        include_sections: List[str] = None
    ) -> Dict:
        """
        Générer un rapport complet avec analyse
        
        Args:
            keyword_ids: Liste des IDs de mots-clés
            days: Période d'analyse en jours
            report_object: Objet/sujet du rapport
            include_sections: Sections à inclure
            
        Returns:
            Dict avec les données du rapport
        """
        from app.models import Keyword, Mention
        from app.influencer_analyzer import InfluencerAnalyzer
        
        # Sections par défaut
        if include_sections is None:
            include_sections = ['analysis', 'influencers']
        
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
        ).all()
        
        report_data = {
            'keywords': keywords_names,
            'keyword_ids': keyword_ids,
            'period_days': days,
            'report_object': report_object or ', '.join(keywords_names),
            'generated_at': datetime.utcnow(),
            'total_mentions': len(mentions),
        }
        
        # Section Analyse
        if 'analysis' in include_sections:
            report_data['analysis'] = self._generate_detailed_analysis(
                mentions, 
                keywords_names,
                days
            )
        
        # Section Influenceurs
        if 'influencers' in include_sections:
            analyzer = InfluencerAnalyzer(self.db)
            # Récupérer tous les influenceurs puis filtrer
            all_influencers = analyzer.get_top_influencers(days=days, limit=50)
            
            # Filtrer les influenceurs pour ces mots-clés
            relevant_influencers = []
            for influencer in all_influencers:
                author_mentions = [
                    m for m in mentions 
                    if m.author == influencer['author'] and m.source == influencer['source']
                ]
                if author_mentions:
                    relevant_influencers.append(influencer)
            
            report_data['influencers'] = relevant_influencers[:10]
        
        return report_data
    
    def _generate_detailed_analysis(
        self, 
        mentions: List,
        keywords: List[str],
        days: int
    ) -> Dict:
        """
        Générer l'analyse détaillée avec réponses aux questions
        """
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
        
        # 1. Est-ce que c'est suivi ?
        is_followed = self._analyze_following(
            mentions, total, days, mentions_per_day, coverage_pct, timeline
        )
        
        # 2. Est-ce que ce n'est pas suivi ?
        is_not_followed = self._analyze_not_following(
            mentions, total, days, coverage_pct
        )
        
        # 3. Comment réagissent les internautes ?
        reactions = self._analyze_reactions(
            mentions, sentiment_dist, sentiment_pct, avg_engagement, total
        )
        
        # 4. Est-ce que les gens adhèrent ?
        adhesion = self._analyze_adhesion(
            sentiment_dist, sentiment_pct, total_with_sentiment
        )
        
        # 5. Est-ce validé par la plupart ? Rejeté ?
        validation = self._analyze_validation(
            sentiment_dist, sentiment_pct, total_with_sentiment
        )
        
        # Synthèse globale
        synthesis = self._generate_synthesis(
            is_followed, is_not_followed, reactions, adhesion, validation,
            total, days, keywords
        )
        
        return {
            'is_followed': is_followed,
            'is_not_followed': is_not_followed,
            'reactions': reactions,
            'adhesion': adhesion,
            'validation': validation,
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
    
    def _analyze_following(
        self, mentions, total, days, mentions_per_day, coverage_pct, timeline
    ) -> Dict:
        """Est-ce que c'est suivi ?"""
        
        # Déterminer si c'est bien suivi
        well_followed = mentions_per_day >= 5 and coverage_pct >= 50
        moderately_followed = mentions_per_day >= 2 and coverage_pct >= 30
        
        if well_followed:
            level = "Très suivi"
            details = (
                f"Le sujet est très activement suivi avec {total} mentions sur {days} jours, "
                f"soit une moyenne de {mentions_per_day:.1f} mentions par jour. "
                f"Une activité a été détectée sur {coverage_pct:.1f}% des jours analysés, "
                f"ce qui indique un suivi régulier et soutenu."
            )
        elif moderately_followed:
            level = "Moyennement suivi"
            details = (
                f"Le sujet est suivi de manière modérée avec {total} mentions sur {days} jours, "
                f"soit {mentions_per_day:.1f} mentions par jour en moyenne. "
                f"Des mentions ont été observées sur {coverage_pct:.1f}% des jours, "
                f"indiquant un intérêt intermittent."
            )
        else:
            level = "Faiblement suivi"
            details = (
                f"Le sujet est peu suivi avec seulement {total} mentions sur {days} jours "
                f"({mentions_per_day:.1f} mentions/jour). "
                f"L'activité n'a été détectée que sur {coverage_pct:.1f}% des jours, "
                f"suggérant un intérêt limité ou sporadique."
            )
        
        return {
            'answer': level,
            'details': details,
            'metrics': {
                'total_mentions': total,
                'daily_average': round(mentions_per_day, 1),
                'coverage_pct': round(coverage_pct, 1),
                'active_days': len(timeline)
            }
        }
    
    def _analyze_not_following(self, mentions, total, days, coverage_pct) -> Dict:
        """Est-ce que ce n'est pas suivi ?"""
        
        if total == 0:
            return {
                'answer': "Absence totale de suivi",
                'details': "Aucune mention n'a été détectée sur la période analysée.",
                'metrics': {'total': 0, 'coverage': 0}
            }
        
        if coverage_pct < 20:
            level = "Suivi très faible"
            details = (
                f"Le suivi est très faible avec seulement {coverage_pct:.1f}% des jours "
                f"présentant de l'activité. Sur {days} jours, on observe de longues périodes "
                f"sans aucune mention, ce qui suggère un désintérêt ou un sujet peu médiatisé."
            )
        elif coverage_pct < 40:
            level = "Suivi irrégulier"
            details = (
                f"Le suivi est irrégulier avec {coverage_pct:.1f}% des jours actifs. "
                f"Il existe des interruptions notables dans l'activité, "
                f"ce qui peut indiquer un intérêt fluctuant ou des pics d'actualité ponctuels."
            )
        else:
            level = "Suivi correct"
            details = (
                f"Le suivi est relativement régulier avec {coverage_pct:.1f}% des jours présentant "
                f"de l'activité. Bien qu'il y ait quelques interruptions, "
                f"l'intérêt semble maintenu sur la période."
            )
        
        return {
            'answer': level,
            'details': details,
            'metrics': {
                'coverage_pct': round(coverage_pct, 1),
                'inactive_pct': round(100 - coverage_pct, 1)
            }
        }
    
    def _analyze_reactions(
        self, mentions, sentiment_dist, sentiment_pct, avg_engagement, total
    ) -> Dict:
        """Comment réagissent les internautes ?"""
        
        # Analyse du sentiment dominant
        dominant_sentiment = max(sentiment_dist.items(), key=lambda x: x[1])[0] if sentiment_dist else 'neutral'
        
        # Niveau d'engagement
        if avg_engagement > 1000:
            engagement_level = "très élevé"
        elif avg_engagement > 500:
            engagement_level = "élevé"
        elif avg_engagement > 100:
            engagement_level = "modéré"
        else:
            engagement_level = "faible"
        
        details = (
            f"Les internautes réagissent avec un engagement {engagement_level} "
            f"(score moyen: {avg_engagement:.1f}). "
            f"Sur le plan émotionnel, "
        )
        
        if sentiment_pct.get('positive', 0) > 50:
            details += (
                f"{sentiment_pct['positive']:.1f}% des réactions sont positives, "
                f"indiquant une réception favorable. "
            )
        elif sentiment_pct.get('negative', 0) > 50:
            details += (
                f"{sentiment_pct['negative']:.1f}% des réactions sont négatives, "
                f"révélant une réception défavorable. "
            )
        else:
            details += (
                f"les réactions sont mitigées avec {sentiment_pct.get('positive', 0):.1f}% positives, "
                f"{sentiment_pct.get('neutral', 0):.1f}% neutres, "
                f"et {sentiment_pct.get('negative', 0):.1f}% négatives. "
            )
        
        # Analyse de la polarisation
        if sentiment_pct.get('neutral', 0) < 20:
            details += "Les opinions sont fortement polarisées avec peu d'indifférence."
        elif sentiment_pct.get('neutral', 0) > 50:
            details += "Une grande partie des internautes restent neutres ou indifférents."
        
        return {
            'answer': f"Engagement {engagement_level}, sentiment {dominant_sentiment}",
            'details': details,
            'metrics': {
                'avg_engagement': round(avg_engagement, 1),
                'engagement_level': engagement_level,
                'positive_pct': round(sentiment_pct.get('positive', 0), 1),
                'neutral_pct': round(sentiment_pct.get('neutral', 0), 1),
                'negative_pct': round(sentiment_pct.get('negative', 0), 1)
            }
        }
    
    def _analyze_adhesion(
        self, sentiment_dist, sentiment_pct, total_with_sentiment
    ) -> Dict:
        """Est-ce que les gens adhèrent ?"""
        
        if total_with_sentiment == 0:
            return {
                'answer': "Indéterminé",
                'details': "Pas assez de données de sentiment pour évaluer l'adhésion.",
                'metrics': {}
            }
        
        positive_pct = sentiment_pct.get('positive', 0)
        negative_pct = sentiment_pct.get('negative', 0)
        
        if positive_pct > 60:
            level = "Forte adhésion"
            details = (
                f"Oui, les gens adhèrent largement avec {positive_pct:.1f}% de réactions positives "
                f"({sentiment_dist['positive']} mentions). "
                f"Seulement {negative_pct:.1f}% expriment un désaccord, "
                f"ce qui témoigne d'une acceptation généralisée."
            )
        elif positive_pct > 40:
            level = "Adhésion modérée"
            details = (
                f"L'adhésion est modérée avec {positive_pct:.1f}% de réactions positives. "
                f"Cependant, {negative_pct:.1f}% de réactions négatives indiquent "
                f"que des réserves ou oppositions existent. "
                f"Le soutien n'est pas unanime mais reste majoritaire."
            )
        elif positive_pct > 25:
            level = "Adhésion faible"
            details = (
                f"L'adhésion est faible avec seulement {positive_pct:.1f}% de soutien. "
                f"Avec {negative_pct:.1f}% de réactions négatives, "
                f"le sujet suscite plus de réserves que d'enthousiasme. "
                f"L'acceptation est limitée à une minorité."
            )
        else:
            level = "Rejet ou indifférence"
            details = (
                f"Les gens n'adhèrent pas avec seulement {positive_pct:.1f}% de soutien. "
                f"Le taux de réactions négatives ({negative_pct:.1f}%) "
                f"ou neutres suggère un rejet ou une indifférence généralisée."
            )
        
        return {
            'answer': level,
            'details': details,
            'metrics': {
                'positive_count': sentiment_dist.get('positive', 0),
                'positive_pct': round(positive_pct, 1),
                'negative_count': sentiment_dist.get('negative', 0),
                'negative_pct': round(negative_pct, 1),
                'adhesion_score': round(positive_pct - negative_pct, 1)
            }
        }
    
    def _analyze_validation(
        self, sentiment_dist, sentiment_pct, total_with_sentiment
    ) -> Dict:
        """Est-ce validé par la plupart ? Rejeté ?"""
        
        if total_with_sentiment == 0:
            return {
                'answer': "Indéterminé",
                'details': "Données insuffisantes pour déterminer la validation.",
                'metrics': {}
            }
        
        positive_pct = sentiment_pct.get('positive', 0)
        negative_pct = sentiment_pct.get('negative', 0)
        neutral_pct = sentiment_pct.get('neutral', 0)
        
        # Ratio approbation/rejet
        if positive_pct + negative_pct > 0:
            approval_ratio = positive_pct / (positive_pct + negative_pct)
        else:
            approval_ratio = 0.5
        
        if positive_pct > 65:
            verdict = "Validé par la majorité"
            details = (
                f"Oui, le sujet est validé par la majorité avec {positive_pct:.1f}% d'approbation "
                f"({sentiment_dist['positive']} mentions positives). "
                f"Seulement {negative_pct:.1f}% le rejettent, "
                f"ce qui représente un ratio d'approbation de {approval_ratio*100:.0f}%. "
                f"Le consensus est clairement favorable."
            )
        elif positive_pct > 45 and approval_ratio > 0.6:
            verdict = "Plutôt validé"
            details = (
                f"Le sujet est plutôt validé avec {positive_pct:.1f}% d'opinions positives "
                f"contre {negative_pct:.1f}% négatives (ratio: {approval_ratio*100:.0f}%). "
                f"Bien qu'une minorité significative le rejette, "
                f"l'acceptation reste dominante."
            )
        elif negative_pct > 50:
            verdict = "Rejeté par la majorité"
            details = (
                f"Non, le sujet est rejeté par la majorité avec {negative_pct:.1f}% de réactions négatives "
                f"({sentiment_dist['negative']} mentions). "
                f"Seulement {positive_pct:.1f}% l'approuvent, "
                f"ce qui indique un rejet clair et majoritaire."
            )
        elif negative_pct > 35:
            verdict = "Fortement contesté"
            details = (
                f"Le sujet est fortement contesté avec {negative_pct:.1f}% de rejet. "
                f"Bien que {positive_pct:.1f}% l'approuvent, "
                f"l'opposition est suffisamment importante pour empêcher un consensus. "
                f"Le sujet reste controversé."
            )
        else:
            verdict = "Ni validé ni rejeté clairement"
            details = (
                f"Le sujet n'est ni clairement validé ni rejeté. "
                f"Avec {positive_pct:.1f}% d'approbation et {negative_pct:.1f}% de rejet, "
                f"les opinions sont équilibrées ou indifférentes ({neutral_pct:.1f}% neutres). "
                f"Aucun consensus ne se dégage."
            )
        
        return {
            'answer': verdict,
            'details': details,
            'metrics': {
                'positive_count': sentiment_dist.get('positive', 0),
                'negative_count': sentiment_dist.get('negative', 0),
                'neutral_count': sentiment_dist.get('neutral', 0),
                'approval_ratio': round(approval_ratio * 100, 1),
                'rejection_ratio': round((1 - approval_ratio) * 100, 1)
            }
        }
    
    def _generate_synthesis(
        self, is_followed, is_not_followed, reactions, adhesion, validation,
        total, days, keywords
    ) -> str:
        """Générer la synthèse finale"""
        
        keywords_str = ', '.join(keywords)
        
        synthesis = (
            f"**Synthèse de l'analyse - {keywords_str}**\n\n"
            f"Sur une période de {days} jours, "
            f"{total} mentions ont été identifiées. "
        )
        
        # Ajout du niveau de suivi
        synthesis += f"{is_followed['answer']}: {is_followed['metrics']['daily_average']} mentions/jour. "
        
        # Ajout de la validation/rejet
        synthesis += f"{validation['answer']} "
        
        # Ajout du sentiment dominant
        if reactions['metrics']['positive_pct'] > 50:
            synthesis += f"avec {reactions['metrics']['positive_pct']:.0f}% de réactions positives. "
        elif reactions['metrics']['negative_pct'] > 50:
            synthesis += f"avec {reactions['metrics']['negative_pct']:.0f}% de réactions négatives. "
        else:
            synthesis += "avec des opinions partagées. "
        
        # Ajout de l'engagement
        synthesis += (
            f"L'engagement moyen est {reactions['metrics']['engagement_level']} "
            f"({reactions['metrics']['avg_engagement']:.0f}). "
        )
        
        # Conclusion sur l'adhésion
        if adhesion['metrics'].get('positive_pct', 0) > 60:
            synthesis += (
                "L'adhésion est forte avec un large soutien de la communauté. "
                "Le sujet bénéficie d'une dynamique favorable."
            )
        elif adhesion['metrics'].get('negative_pct', 0) > 50:
            synthesis += (
                "L'adhésion est faible avec une opposition significative. "
                "Le sujet fait face à des réticences marquées."
            )
        else:
            synthesis += (
                "L'adhésion est modérée avec des avis partagés. "
                "Le sujet nécessite un effort de communication supplémentaire."
            )
        
        return synthesis
    
    def generate_html_report(self, report_data: Dict) -> str:
        """
        Générer le HTML du rapport (format 2 pages)
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 1.5cm;
                }}
                
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #333;
                    line-height: 1.4;
                    font-size: 11pt;
                }}
                
                .header {{
                    text-align: center;
                    padding: 15px 0;
                    border-bottom: 3px solid #667eea;
                    margin-bottom: 20px;
                }}
                
                .header h1 {{
                    color: #667eea;
                    font-size: 20pt;
                    margin: 0 0 5px 0;
                }}
                
                .header .subtitle {{
                    color: #666;
                    font-size: 10pt;
                }}
                
                .info-box {{
                    background: #f5f7ff;
                    border-left: 4px solid #667eea;
                    padding: 10px 15px;
                    margin: 15px 0;
                    font-size: 10pt;
                }}
                
                .section {{
                    margin: 15px 0;
                    page-break-inside: avoid;
                }}
                
                .section-title {{
                    color: #667eea;
                    font-size: 13pt;
                    font-weight: bold;
                    margin: 15px 0 8px 0;
                    padding-bottom: 5px;
                    border-bottom: 2px solid #e5e7eb;
                }}
                
                .question {{
                    background: #f9fafb;
                    padding: 8px 12px;
                    margin: 8px 0;
                    border-left: 3px solid #667eea;
                    font-size: 10pt;
                }}
                
                .question .q {{
                    font-weight: bold;
                    color: #667eea;
                    margin-bottom: 5px;
                }}
                
                .question .answer {{
                    font-weight: bold;
                    color: #1f2937;
                    margin: 5px 0;
                }}
                
                .question .details {{
                    color: #4b5563;
                    line-height: 1.5;
                }}
                
                .metrics {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                    margin: 10px 0;
                }}
                
                .metric {{
                    background: white;
                    border: 1px solid #e5e7eb;
                    padding: 8px;
                    text-align: center;
                    border-radius: 5px;
                }}
                
                .metric-value {{
                    font-size: 16pt;
                    font-weight: bold;
                    color: #667eea;
                }}
                
                .metric-label {{
                    font-size: 9pt;
                    color: #6b7280;
                }}
                
                .synthesis {{
                    background: linear-gradient(135deg, #667eea15, #764ba215);
                    border: 2px solid #667eea;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 8px;
                    font-size: 10pt;
                    line-height: 1.6;
                }}
                
                .synthesis strong {{
                    color: #667eea;
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 10px 0;
                    font-size: 9pt;
                }}
                
                th {{
                    background: #667eea;
                    color: white;
                    padding: 8px;
                    text-align: left;
                    font-weight: bold;
                }}
                
                td {{
                    padding: 6px 8px;
                    border-bottom: 1px solid #e5e7eb;
                }}
                
                tr:nth-child(even) {{
                    background: #f9fafb;
                }}
                
                .page-break {{
                    page-break-after: always;
                }}
                
                .footer {{
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    text-align: center;
                    font-size: 8pt;
                    color: #9ca3af;
                    padding: 10px;
                    border-top: 1px solid #e5e7eb;
                }}
            </style>
        </head>
        <body>
            <!-- PAGE 1: ANALYSE -->
            <div class="header">
                <h1>📊 RAPPORT D'ANALYSE</h1>
                <div class="subtitle">
                    Objet: <strong>{report_data['report_object']}</strong><br>
                    Période: {report_data['period_days']} jours | 
                    Généré le: {report_data['generated_at'].strftime('%d/%m/%Y à %H:%M')}
                </div>
            </div>
            
            <div class="info-box">
                <strong>Mots-clés analysés:</strong> {', '.join(report_data['keywords'])}<br>
                <strong>Total mentions:</strong> {report_data['total_mentions']} | 
                <strong>Période:</strong> {report_data['period_days']} jours
            </div>
        """
        
        # Section Analyse
        if 'analysis' in report_data:
            analysis = report_data['analysis']
            metrics = analysis['metrics']
            
            html += """
            <div class="section-title">📈 ANALYSE DÉTAILLÉE</div>
            
            <!-- Métriques clés -->
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Mentions/jour</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{}%</div>
                    <div class="metric-label">Couverture</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Engagement moyen</div>
                </div>
            </div>
            """.format(
                metrics['mentions_per_day'],
                metrics['coverage_percentage'],
                int(metrics['avg_engagement'])
            )
            
            # Questions et réponses
            questions = [
                ('is_followed', "Est-ce que c'est suivi ?"),
                ('is_not_followed', "Est-ce que ce n'est pas suivi ?"),
                ('reactions', "Comment réagissent les internautes ?"),
                ('adhesion', "Est-ce que les gens adhèrent ?"),
                ('validation', "Est-ce validé par la plupart ? Rejeté ?"),
            ]
            
            for key, question in questions:
                if key in analysis:
                    data = analysis[key]
                    html += f"""
            <div class="question">
                <div class="q">❓ {question}</div>
                <div class="answer">➤ {data['answer']}</div>
                <div class="details">{data['details']}</div>
            </div>
                    """
            
            # Synthèse
            html += f"""
            <div class="section-title">💡 SYNTHÈSE</div>
            <div class="synthesis">
                {analysis['synthesis']}
            </div>
            """
        
        html += '<div class="page-break"></div>'
        
        # PAGE 2: INFLUENCEURS
        if 'influencers' in report_data and report_data['influencers']:
            html += """
            <div class="header">
                <h1>👑 TOP INFLUENCEURS</h1>
                <div class="subtitle">Comptes générant le plus d'engagement</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Auteur</th>
                        <th>Source</th>
                        <th>Mentions</th>
                        <th>Engagement Total</th>
                        <th>Engagement Moy</th>
                        <th>Sentiment</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for i, influencer in enumerate(report_data['influencers'][:15], 1):
                sentiment_emoji = '😊' if influencer['sentiment_score'] >= 70 else '😐' if influencer['sentiment_score'] >= 40 else '😞'
                
                html += f"""
                    <tr>
                        <td><strong>{i}</strong></td>
                        <td>{influencer['author']}</td>
                        <td>{influencer['source'].upper()}</td>
                        <td>{influencer['mention_count']}</td>
                        <td>{self._format_number(influencer['total_engagement'])}</td>
                        <td>{self._format_number(influencer['avg_engagement'])}</td>
                        <td>{sentiment_emoji} {influencer['sentiment_score']:.0f}%</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
        
        html += """
            <div class="footer">
                Rapport généré par Superviseur MINDEF | Confidentiel - Usage interne uniquement
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_pdf(self, report_data: Dict) -> bytes:
        """
        Générer le PDF du rapport
        """
        try:
            from weasyprint import HTML
            
            html_content = self.generate_html_report(report_data)
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            return pdf_bytes
            
        except ImportError:
            logger.warning("WeasyPrint not available, generating HTML only")
            html_content = self.generate_html_report(report_data)
            return html_content.encode('utf-8')
    
    def _format_number(self, num: float) -> str:
        """Formater un nombre pour affichage"""
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        return str(round(num))